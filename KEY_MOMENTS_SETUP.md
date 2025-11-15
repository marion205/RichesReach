# Key Moments Feature - Setup Guide

## Overview

The Key Moments feature provides an AI-powered, interactive stock chart experience that's superior to Public.com's implementation. It includes:

- **Smart Storylines**: Continuous narrative as users scrub the chart
- **DeepContext™**: Multi-layer moments (quick summary → deeper context → personalized analysis)
- **Moment Clusters**: Visual grouping of related events
- **Voice Mode**: AI voice coach reads chart stories aloud
- **Story Mode**: Cinematic timeline experience with auto-scroll

## What Was Created

### Backend (Django)

1. **Model**: `deployment_package/backend/core/models.py`
   - `StockMoment` model with all required fields
   - `MomentCategory` choices enum

2. **GraphQL Types**: `deployment_package/backend/core/types.py`
   - `StockMomentType` - GraphQL type for moments
   - `MomentCategoryEnum` - Category enum
   - `ChartRangeEnum` - Time range enum

3. **GraphQL Query**: `deployment_package/backend/core/queries.py`
   - `stock_moments` query with symbol and range parameters
   - `resolve_stock_moments` resolver

4. **Worker**: `deployment_package/backend/core/stock_moment_worker.py`
   - Python worker that processes raw moment jobs
   - Calls OpenAI API to generate moment summaries
   - Saves to database

### Frontend (React Native)

1. **ChartWithMoments**: `mobile/src/components/charts/ChartWithMoments.tsx`
   - Interactive chart with moment dots
   - Gesture-based moment selection
   - Moment cards with quick summaries

2. **MomentStoryPlayer**: `mobile/src/components/charts/MomentStoryPlayer.tsx`
   - Voice narration using expo-speech
   - Auto-scrolling story mode
   - Play/pause/next/previous controls

3. **Integration Example**: `mobile/src/features/stocks/screens/StockMomentsIntegration.tsx`
   - GraphQL query setup
   - Complete integration example

## Setup Steps

### 1. Database Migration

```bash
cd deployment_package/backend
python manage.py makemigrations core
python manage.py migrate
```

### 2. Install Frontend Dependencies

```bash
cd mobile
npx expo install expo-speech
npm install react-native-svg  # If not already installed
```

### 3. Integrate into StockDetailScreen

Add to `mobile/src/features/stocks/screens/StockDetailScreen.tsx`:

```typescript
import { StockMomentsIntegration } from './StockMomentsIntegration';

// In ChartRoute component, after the chart:
<StockMomentsIntegration
  symbol={symbol}
  priceSeries={processedData.map(d => ({
    timestamp: d.timestamp,
    price: d.close
  }))}
  chartRange="THREE_MONTHS" // or based on timeframe
/>
```

### 4. Configure Worker

The worker (`stock_moment_worker.py`) needs:

- `OPENAI_API_KEY` environment variable set
- A way to fetch `RawMomentJob` objects (implement `fetch_pending_jobs()`)

Example job creation:

```python
from core.stock_moment_worker import (
    RawMomentJob, PriceContext, Event, create_stock_moment_from_job
)
from datetime import datetime

job = RawMomentJob(
    symbol="AAPL",
    timestamp=datetime.now(),
    price_context=PriceContext(
        start_price=150.0,
        end_price=155.0,
        pct_change=3.33,
        volume_vs_average="2.3x average"
    ),
    events=[
        Event(
            type="EARNINGS",
            time=datetime.now(),
            headline="Apple Reports Strong Q4 Earnings",
            summary="Beat estimates by 5%",
            url="https://example.com/news"
        )
    ]
)

moment = create_stock_moment_from_job(job)
```

### 5. Run Worker

```bash
cd deployment_package/backend
python core/stock_moment_worker.py
```

Or set up as a Celery task, cron job, or ECS task.

## GraphQL Query Example

```graphql
query GetStockMoments($symbol: String!, $range: ChartRangeEnum!) {
  stockMoments(symbol: $symbol, range: $range) {
    id
    symbol
    timestamp
    category
    title
    quickSummary
    deepSummary
    importanceScore
    sourceLinks
    impact1D
    impact7D
  }
}
```

## Features

### Interactive Chart
- Drag finger across chart to explore moments
- Moment dots highlight on the chart
- Quick summary cards appear below chart
- Tap card for full deep summary

### Story Mode
- Tap "Play Story" button
- Voice narration reads each moment
- Auto-advances through moments
- Chart highlights active moment
- Swipeable cards with full context

### Voice Integration
- Uses device TTS (expo-speech)
- Configurable rate and pitch
- Auto-advances after narration
- Pause/resume controls

## Next Steps

1. **Populate Moments**: Create a service that:
   - Monitors price movements
   - Fetches news/earnings/insider data
   - Creates `RawMomentJob` objects
   - Feeds to worker

2. **Enhance UI**: 
   - Add moment clusters visualization
   - Add haptic feedback
   - Add animations
   - Add budget/life context integration

3. **Performance**:
   - Cache moments in Redis
   - Batch GraphQL queries
   - Optimize chart rendering

4. **Analytics**:
   - Track which moments users view
   - Measure engagement with story mode
   - A/B test different moment formats

## Testing

Test the GraphQL query:

```bash
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { stockMoments(symbol: \"AAPL\", range: THREE_MONTHS) { id title quickSummary } }"
  }'
```

Test the worker:

```python
python deployment_package/backend/core/stock_moment_worker.py
```

## Notes

- Moments with `importance_score <= 0.05` are automatically filtered out
- The worker uses `gpt-4o-mini` by default (change in `stock_moment_worker.py`)
- Voice narration requires `expo-speech` to be installed
- Chart component uses `react-native-svg` for rendering

