package main

import (
	"context"
	"log"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	nats "github.com/nats-io/nats.go"

	"github.com/novaspark/k8s-order-api/handlers"
	"github.com/novaspark/k8s-order-api/store"
)

func main() {
	ctx := context.Background()

	// ── Redis ────────────────────────────────────────────────────────────────
	redisAddr := getenv("REDIS_ADDR", "localhost:6379")
	s := store.New(redisAddr)
	if err := s.Ping(ctx); err != nil {
		log.Fatalf("Redis connect failed (%s): %v", redisAddr, err)
	}
	log.Printf("Connected to Redis at %s", redisAddr)

	// ── NATS ─────────────────────────────────────────────────────────────────
	natsURL := getenv("NATS_URL", "nats://localhost:4222")
	nc, err := nats.Connect(natsURL,
		nats.RetryOnFailedConnect(true),
		nats.MaxReconnects(-1),
		nats.ReconnectWait(2*time.Second),
	)
	if err != nil {
		log.Fatalf("NATS connect failed (%s): %v", natsURL, err)
	}
	defer nc.Close()
	log.Printf("Connected to NATS at %s", natsURL)

	// ── HTTP server ───────────────────────────────────────────────────────────
	r := gin.Default()
	h := handlers.New(s, nc)
	h.RegisterRoutes(r)

	port := getenv("PORT", "8080")
	log.Printf("API listening on :%s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("server error: %v", err)
	}
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
