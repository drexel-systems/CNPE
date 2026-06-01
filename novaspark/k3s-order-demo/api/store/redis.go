package store

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/novaspark/k8s-order-api/models"
	"github.com/redis/go-redis/v9"
)

// Store is the interface the handlers depend on.
// Defining it here (with the producer) keeps the store package self-contained.
// Handlers import this interface rather than the concrete type, which makes
// the handlers independently testable with a fake implementation.
type Store interface {
	Get(ctx context.Context, id string) (*models.Order, error)
	List(ctx context.Context) ([]models.Order, error)
	Save(ctx context.Context, order *models.Order) error
	Ping(ctx context.Context) error
}

// RedisStore is the production implementation of Store backed by Redis.
type RedisStore struct {
	client *redis.Client
}

// New returns a connected RedisStore.
func New(addr string) *RedisStore {
	return &RedisStore{
		client: redis.NewClient(&redis.Options{Addr: addr}),
	}
}

// Ping checks the Redis connection — used at startup.
func (s *RedisStore) Ping(ctx context.Context) error {
	return s.client.Ping(ctx).Err()
}

// Get retrieves a single order by ID.
// Returns redis.Nil (wrapped) when the key does not exist so callers can
// distinguish "not found" from a genuine Redis error.
func (s *RedisStore) Get(ctx context.Context, id string) (*models.Order, error) {
	val, err := s.client.Get(ctx, key(id)).Result()
	if err == redis.Nil {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("redis get: %w", err)
	}

	var order models.Order
	if err := json.Unmarshal([]byte(val), &order); err != nil {
		return nil, fmt.Errorf("unmarshal order: %w", err)
	}
	return &order, nil
}

// List returns all orders by fetching the ID set, then fetching each record.
// Equivalent to a DynamoDB Scan — fine at demo scale, not at millions of records.
func (s *RedisStore) List(ctx context.Context) ([]models.Order, error) {
	ids, err := s.client.SMembers(ctx, "orders").Result()
	if err != nil {
		return nil, fmt.Errorf("redis smembers: %w", err)
	}

	orders := make([]models.Order, 0, len(ids))
	for _, id := range ids {
		o, err := s.Get(ctx, id)
		if err != nil {
			continue // skip missing records gracefully
		}
		orders = append(orders, *o)
	}
	return orders, nil
}

// Save writes an order to Redis and ensures its ID is in the tracking set.
// Used for both initial persistence (by the worker) and updates (by handlers).
// A pipeline keeps the SET + SADD atomic from a latency standpoint.
func (s *RedisStore) Save(ctx context.Context, order *models.Order) error {
	payload, err := json.Marshal(order)
	if err != nil {
		return fmt.Errorf("marshal order: %w", err)
	}

	pipe := s.client.Pipeline()
	pipe.Set(ctx, key(order.OrderID), payload, 0)
	pipe.SAdd(ctx, "orders", order.OrderID)
	if _, err := pipe.Exec(ctx); err != nil {
		return fmt.Errorf("redis pipeline: %w", err)
	}
	return nil
}

// ── Sentinel errors ───────────────────────────────────────────────────────────

// ErrNotFound is returned by Get when the order ID does not exist.
// Handlers check for this specifically to return 404 vs 500.
var ErrNotFound = fmt.Errorf("order not found")

// ── helpers ───────────────────────────────────────────────────────────────────

func key(id string) string {
	return "order:" + id
}
