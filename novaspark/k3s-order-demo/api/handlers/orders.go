package handlers

import (
	"context"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	nats "github.com/nats-io/nats.go"

	"github.com/novaspark/k8s-order-api/models"
	"github.com/novaspark/k8s-order-api/store"
)

// Handler holds the dependencies every route handler needs.
// Injecting them here (rather than using package-level globals) makes
// each handler independently testable — swap in a fake store and a nil
// NATS connection and the handler logic can be verified without a cluster.
type Handler struct {
	store store.Store
	nc    *nats.Conn
}

// New returns a Handler wired to the given store and NATS connection.
func New(s store.Store, nc *nats.Conn) *Handler {
	return &Handler{store: s, nc: nc}
}

// RegisterRoutes attaches all order routes to the given Gin engine.
func (h *Handler) RegisterRoutes(r *gin.Engine) {
	r.POST("/orders", h.SubmitOrder)
	r.GET("/orders", h.ListOrders)
	r.GET("/orders/:id", h.GetOrder)
	r.PATCH("/orders/:id", h.UpdateOrder)
	r.DELETE("/orders/:id", h.DeleteOrder)
}

// ── POST /orders ──────────────────────────────────────────────────────────────

// SubmitOrder accepts a new order, publishes it to NATS, and returns 202.
// Persistence happens asynchronously via the worker — same pattern as
// API Gateway → SQS → Lambda processor in the serverless version.
func (h *Handler) SubmitOrder(c *gin.Context) {
	var req models.CreateOrderRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	order := models.Order{
		OrderID:   uuid.New().String(),
		Item:      req.Item,
		Quantity:  req.Quantity,
		Status:    "received",
		CreatedAt: time.Now().UTC(),
		UpdatedAt: time.Now().UTC(),
	}

	payload, err := json.Marshal(order)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to encode order"})
		return
	}

	if err := h.nc.Publish("orders.new", payload); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to queue order"})
		return
	}

	log.Printf("order %s queued (item: %s qty: %d)", order.OrderID, order.Item, order.Quantity)

	c.JSON(http.StatusAccepted, gin.H{
		"order_id": order.OrderID,
		"status":   "received",
		"message":  "order queued for processing",
	})
}

// ── GET /orders/:id ───────────────────────────────────────────────────────────

func (h *Handler) GetOrder(c *gin.Context) {
	order, err := h.store.Get(context.Background(), c.Param("id"))
	if errors.Is(err, store.ErrNotFound) {
		c.JSON(http.StatusNotFound, gin.H{"error": "order not found"})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to retrieve order"})
		return
	}
	c.JSON(http.StatusOK, order)
}

// ── GET /orders ───────────────────────────────────────────────────────────────

func (h *Handler) ListOrders(c *gin.Context) {
	orders, err := h.store.List(context.Background())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to list orders"})
		return
	}
	c.JSON(http.StatusOK, orders)
}

// ── PATCH /orders/:id ─────────────────────────────────────────────────────────

// UpdateOrder allows a client to advance an order's status.
// Only "processing" and "shipped" are valid values — "received" is set on
// creation and "cancelled" is reserved for soft-delete via DELETE.
func (h *Handler) UpdateOrder(c *gin.Context) {
	var req models.UpdateOrderRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if !models.ValidStatuses[req.Status] {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "invalid status — must be one of: processing, shipped",
		})
		return
	}

	ctx := context.Background()
	order, err := h.store.Get(ctx, c.Param("id"))
	if errors.Is(err, store.ErrNotFound) {
		c.JSON(http.StatusNotFound, gin.H{"error": "order not found"})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to retrieve order"})
		return
	}

	order.Status = req.Status
	order.UpdatedAt = time.Now().UTC()

	if err := h.store.Save(ctx, order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to update order"})
		return
	}

	log.Printf("order %s updated → %s", order.OrderID, order.Status)
	c.JSON(http.StatusOK, order)
}

// ── DELETE /orders/:id ────────────────────────────────────────────────────────

// DeleteOrder soft-deletes an order by setting its status to "cancelled".
// The record is kept in Redis — the audit trail is preserved, same design
// decision as the NovaSpark AWS version (DynamoDB record survives with
// status: cancelled rather than being removed).
func (h *Handler) DeleteOrder(c *gin.Context) {
	ctx := context.Background()
	order, err := h.store.Get(ctx, c.Param("id"))
	if errors.Is(err, store.ErrNotFound) {
		c.JSON(http.StatusNotFound, gin.H{"error": "order not found"})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to retrieve order"})
		return
	}

	order.Status = "cancelled"
	order.UpdatedAt = time.Now().UTC()

	if err := h.store.Save(ctx, order); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to cancel order"})
		return
	}

	log.Printf("order %s cancelled (soft delete)", order.OrderID)
	c.JSON(http.StatusOK, order)
}
