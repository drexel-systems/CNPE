package handlers

import (
	"log"
	"os"

	"github.com/gin-gonic/gin"
)

// RegisterDebugRoutes attaches the chaos / resilience demo endpoints.
// These exist solely to demonstrate Kubernetes pod self-healing in lecture.
// Both GET and POST are registered so the endpoints can be triggered from a
// browser (GET) as well as curl (POST).
//
// Do not ship these in a production binary.
func (h *Handler) RegisterDebugRoutes(r *gin.Engine) {
	r.GET("/crash", h.Crash)
	r.POST("/crash", h.Crash)
	r.GET("/panic", h.Panic)
	r.POST("/panic", h.Panic)
}

// Crash simulates an unexpected hard crash — the process calls os.Exit(1)
// immediately with no log output, as if something catastrophic happened with
// no warning (segfault, OOM kill, unhandled signal, etc.).
//
// The caller receives a connection reset / EOF because the process dies before
// it can write an HTTP response. Kubernetes detects the non-zero exit code,
// restarts the container, and the readiness probe gates traffic until the
// pod is healthy again.
func (h *Handler) Crash(c *gin.Context) {
	os.Exit(1)
}

// Panic simulates a deliberate shutdown after the application discovers a
// state it cannot safely recover from — for example, detecting data corruption
// or a dependency that has become fatally inconsistent.
//
// Unlike Crash, it emits a forensic log message before exiting so that
// operators (and students) can see the reason in kubectl logs after the pod
// restarts. log.Fatal prints the message then calls os.Exit(1).
func (h *Handler) Panic(c *gin.Context) {
	log.Fatal("PANIC: application entered an unrecoverable state — " +
		"detected fatal inconsistency, forcing shutdown for safety. " +
		"Review recent orders for data integrity issues.")
}
