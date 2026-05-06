# demo-api-testing

> Suite de tests de API para [demo-backend-api](https://github.com/JonathanIzquierdo/demo-backend-api).

Este es el repo de QA. Los tests son **gestionados (generados, mantenidos y reparados) por [QAEngineerAgent](https://github.com/JonathanIzquierdo/QAEngineerAgent)**.

## Estructura

```
demo-api-testing/
├── postman/
│   └── demo-backend-api.postman_collection.json   ← collection generada/mantenida por el agente
├── .qa-agent/
│   └── state.json                                 ← memoria del agente (qué endpoints ya tiene cubiertos)
├── .github/workflows/
│   └── run-tests.yml                              ← corre la suite con Newman en CI
├── reports/                                        ← outputs de los runs (coverage, métricas)
└── README.md
```

## Cómo funciona el ciclo

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│  demo-backend-api    │     │  QAEngineerAgent     │     │  demo-api-testing    │
│  (producto)          │     │  (servicio agéntico) │     │  (este repo)         │
│                      │     │                      │     │                      │
│  1. Cambia un        │ ──► │  2. Lee diff /       │ ──► │  3. Abre PR con      │
│     endpoint o       │     │     openapi.json     │     │     tests nuevos /   │
│     schema           │     │                      │     │     actualizados     │
└──────────────────────┘     └──────────────────────┘     └──────────────────────┘
                                                                     │
                                                                     ▼
                                                          ┌──────────────────────┐
                                                          │  4. CI corre Newman  │
                                                          │     contra el back   │
                                                          │     y reporta        │
                                                          └──────────────────────┘
```

## Correr los tests local

```bash
npm install -g newman
newman run postman/demo-backend-api.postman_collection.json \
  --env-var "baseUrl=http://localhost:8000" \
  --env-var "authToken=demo-token-123"
```

## Métricas

Cada run de CI publica:
- **Total tests**: cuántos casos se corrieron
- **Pass rate**: % que pasaron
- **Coverage**: % de endpoints del openapi.json que tienen al menos 1 test asociado
- **Tiempo total**: duración del run

Ver el último report en [Actions → Run Tests](https://github.com/JonathanIzquierdo/demo-api-testing/actions).

## Para qué sirve este repo

Es el destino de los PRs que abre `QAEngineerAgent`. En el workshop:

1. Disparás `Full Scan` en `QAEngineerAgent` apuntado a `demo-backend-api`
2. El agente analiza el OpenAPI, ve que no hay tests acá, y abre un PR con la collection inicial
3. Mergeás → CI corre Newman y reporta métricas
4. En `demo-backend-api` cambiás un schema → el agente abre un PR acá ajustando los tests afectados
