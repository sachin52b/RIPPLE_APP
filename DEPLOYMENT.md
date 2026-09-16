# Permanent deployment

This project is prepared as a single Docker web service. The FastAPI service
serves both the API and the compiled React application, so deployment creates
one stable public URL.

## Render deployment

1. Create a private or public GitHub repository and push this project.
2. In Render, select **New +** → **Blueprint**, then connect the repository.
3. Render discovers `render.yaml`; approve the `financial-contagion-resilience-lab` web service.
4. Wait for the Docker build and open the generated HTTPS URL.
5. Verify `<your-url>/api/health` returns `status: ok`, then share `<your-url>`.

## Important operational note

The application currently keeps active simulation sessions in process memory
and saves run records to the local container filesystem. Those records survive
for the active process but may be lost when a cloud host restarts or redeploys
the service. For a durable production audit history, connect `RunStore` to a
managed database or persistent disk before collecting real user data.
