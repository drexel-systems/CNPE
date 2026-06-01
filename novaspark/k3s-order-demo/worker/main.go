package main

import (
	"context"
	"encoding/json"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	nats "github.com/nats-io/nats.go"
	"github.com/redis/go-redis/v9"
)

// Order must match the API's Order struct exactly — both services share
// the same JSON contract over NATS, just as Lambda + SQS share a message schema.
type Order struct {
	OrderID   string    `json:"order_id"`
	Item      string    `json:"item"`
	Quantity  int       `json:"quantity"`
	Status    string    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

var (
	rdb *redis.Client
	ctx = context.Background()
)

func main() {
	// ── Redis connection ─────────────────────────────────────────────────────
	redisAddr := getenv("REDIS_ADDR", "localhost:6379")
	rdb = redis.NewClient(&redis.Options{Addr: redisAddr})
	if err := rdb.Ping(ctx).Err(); err != nil {
		log.Fatalf("Redis connect failed (%s): %v", redisAddr, err)
	}
	log.Printf("Connected to Redis at %s", redisAddr)

	// ── NATS connection ──────────────────────────────────────────────────────
	natsURL := getenv("NATS_URL", "nats://localhost:4222")
	nc, err := nats.Connect(natsURL,
		nats.RetryOnFailedConnect(true),
		nats.MaxReconnects(-1), // retry forever — pod restarts are normal in k8s
		nats.ReconnectWait(2*time.Second),
	)
	if err != nil {
		log.Fatalf("NATS connect failed (%s): %v", natsURL, err)
	}
	defer nc.Drain()
	log.Printf("Connected to NATS at %s", natsURL)

	// ── Subscribe ────────────────────────────────────────────────────────────
	// orders.new is the NATS subject — equivalent to the SQS queue in the
	// serverless architecture. The worker is the processor Lambda equivalent.
	sub, err := nc.Subscribe("orders.new", processOrder)
	if err != nil {
		log.Fatalf("NATS subscribe failed: %v", err)
	}
	defer sub.Unsubscribe()

	log.Println("Worker ready — listening on orders.new")

	// ── Graceful shutdown ────────────────────────────────────────────────────
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Shutdown signal received — draining...")
}

// processOrder is the NATS message handler. It mirrors the SQS processor
// Lambda: unmarshal the payload, update status, persist to the backing store.
func processOrder(msg *nats.Msg) {
	var order Order
	if err := json.Unmarshal(msg.Data, &order); err != nil {
		log.Printf("ERROR: failed to unmarshal message: %v — skipping", err)
		return
	}

	// Advance status from received → processing
	order.Status = "processing"
	order.UpdatedAt = time.Now().UTC()

	payload, err := json.Marshal(order)
	if err != nil {
		log.Printf("ERROR: failed to re-marshal order %s: %v", order.OrderID, err)
		return
	}

	// Persist: store the order JSON and add its ID to the tracking set.
	// Redis pipeline keeps both writes atomic from a latency standpoint.
	pipe := rdb.Pipeline()
	pipe.Set(ctx, "order:"+order.OrderID, payload, 0)
	pipe.SAdd(ctx, "orders", order.OrderID)
	if _, err := pipe.Exec(ctx); err != nil {
		log.Printf("ERROR: Redis write failed for order %s: %v", order.OrderID, err)
		return
	}

	log.Printf("order %s persisted (item: %s qty: %d)", order.OrderID, order.Item, order.Quantity)
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
