package models

import "time"

// Order is the core domain type shared across handlers, store, and NATS messages.
type Order struct {
	OrderID   string    `json:"order_id"`
	Item      string    `json:"item"`
	Quantity  int       `json:"quantity"`
	Status    string    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// CreateOrderRequest is the body expected on POST /orders.
type CreateOrderRequest struct {
	Item     string `json:"item"     binding:"required"`
	Quantity int    `json:"quantity" binding:"required,min=1"`
}

// UpdateOrderRequest is the body expected on PATCH /orders/:id.
// Only Status is patchable — item and quantity are immutable after submission.
type UpdateOrderRequest struct {
	Status string `json:"status" binding:"required"`
}

// ValidStatuses are the values a client may set via PATCH.
// "received" is set on creation; "cancelled" is reserved for soft-delete (DELETE).
var ValidStatuses = map[string]bool{
	"processing": true,
	"shipped":    true,
}
