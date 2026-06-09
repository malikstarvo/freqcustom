FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod ./
COPY *.go ./
RUN go mod tidy && go mod download
RUN CGO_ENABLED=0 GOOS=linux go build -o collector .

FROM alpine:3.20
RUN apk add --no-cache ca-certificates tzdata
COPY --from=builder /app/collector /usr/local/bin/collector
ENV TIMESCALE_DSN="postgresql://freqtrade:freqtrade@timescaledb:5432/freqtrade?sslmode=disable"
CMD ["collector"]
