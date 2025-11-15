# Key Moments Feature - Complete Architecture

## 🎯 Overview

Yes, we **are using GenAI (OpenAI GPT-4o-mini)** to generate the stock moments! Here's the complete flow:

## 📊 Data Flow

```
1. Raw Market Data (Price, Volume, Events)
   ↓
2. stock_moment_worker.py (Python Worker)
   ↓
3. OpenAI GPT-4o-mini API
   ↓
4. StockMoment Django Model (Database)
   ↓
5. GraphQL API (queries.py)
   ↓
6. React Native Frontend (StockMomentsIntegration)
   ↓
7. ChartWithMoments + MomentStoryPlayer (UI)
```

---

## 🤖 Backend: AI Generation (GenAI)

### File: `deployment_package/backend/core/stock_moment_worker.py`

This is where **OpenAI GPT-4o-mini** generates the moments:

```python
from openai import OpenAI

client = OpenAI()  # uses OPENAI_API_KEY env var

SYSTEM_MESSAGE = """You are an expert financial journalist and educator.
Your job is to explain important stock price movements in clear, 
simple language that a beginner can understand in under 30 seconds.
...
"""

def call_llm_for_moment(job: RawMomentJob) -> dict:
    # Build prompt with price context and events
    user_message = USER_TEMPLATE.format(
        symbol=job.symbol,
        timestamp=job.timestamp.isoformat(),
        start_price=price_ctx.start_price,
        end_price=price_ctx.end_price,
        pct_change=price_ctx.pct_change,
        volume_vs_average=price_ctx.volume_vs_average,
        events_block=events_block,
    )

    # Call OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # GenAI model
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user_message},
        ],
    )

    # Parse JSON response
    data = json.loads(response.choices[0].message.content)
    return data  # Contains: title, quick_summary, deep_summary, category, importance_score
```

**Key Points:**
- ✅ Uses **OpenAI GPT-4o-mini** (configurable to GPT-4o or GPT-5)
- ✅ Generates JSON with structured data
- ✅ Filters by `importance_score` (only saves moments > 0.05)
- ✅ Categorizes moments (EARNINGS, NEWS, INSIDER, MACRO, SENTIMENT, OTHER)

---

## 💾 Backend: Database Model

### File: `deployment_package/backend/core/models.py`

```python
class MomentCategory(models.TextChoices):
    EARNINGS = "EARNINGS", "Earnings"
    NEWS = "NEWS", "News"
    INSIDER = "INSIDER", "Insider"
    MACRO = "MACRO", "Macro"
    SENTIMENT = "SENTIMENT", "Sentiment"
    OTHER = "OTHER", "Other"

class StockMoment(models.Model):
    """AI-generated key moments for stock price movements"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    symbol = models.CharField(max_length=16, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    
    importance_score = models.FloatField(default=0.0)
    category = models.CharField(max_length=32, choices=MomentCategory.choices)
    
    title = models.CharField(max_length=140)
    quick_summary = models.TextField()      # For chart tooltips
    deep_summary = models.TextField()       # For voice narration
    
    source_links = models.JSONField(default=list, blank=True)
    impact_1d = models.FloatField(null=True, blank=True)
    impact_7d = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 🔌 Backend: GraphQL API

### File: `deployment_package/backend/core/queries.py`

```python
class Query(graphene.ObjectType):
    # ... other queries ...
    stock_moments = graphene.List(
        StockMomentType,
        symbol=graphene.String(required=True),
        range=graphene.Argument(ChartRangeEnum, required=True),
    )

def resolve_stock_moments(self, info, symbol, range):
    """Resolve stock moments for a given symbol and time range"""
    try:
        now = timezone.now()
        symbol_upper = symbol.upper()
        
        # Calculate start date based on range
        if range == ChartRangeEnum.ONE_MONTH:
            start = now - timedelta(days=30)
        elif range == ChartRangeEnum.THREE_MONTHS:
            start = now - timedelta(days=90)
        # ... other ranges ...
        
        # Query moments from database
        moments = StockMoment.objects.filter(
            symbol=symbol_upper,
            timestamp__gte=start
        ).order_by('timestamp')
        
        return list(moments)
    except Exception as e:
        logger.error(f"Error resolving stock moments for {symbol}: {e}")
        return []
```

### File: `deployment_package/backend/core/types.py`

```python
class StockMomentType(DjangoObjectType):
    """GraphQL type for stock moments"""
    category = graphene.Field(MomentCategoryEnum)
    importanceScore = graphene.Float()
    quickSummary = graphene.String()
    deepSummary = graphene.String()
    sourceLinks = graphene.List(graphene.String)
    impact1D = graphene.Float()
    impact7D = graphene.Float()
    
    class Meta:
        model = StockMoment
        fields = (
            "id", "symbol", "timestamp", "importance_score",
            "category", "title", "quick_summary", "deep_summary",
            "source_links", "impact_1d", "impact_7d",
        )
```

---

## 📱 Frontend: GraphQL Query

### File: `mobile/src/features/stocks/screens/StockMomentsIntegration.tsx`

```typescript
const GET_STOCK_MOMENTS = gql`
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
`;

export const StockMomentsIntegration: React.FC<StockMomentsIntegrationProps> = ({
  symbol,
  priceSeries,
  chartRange,
}) => {
  // Query stock moments from GraphQL
  const { data, loading, error } = useQuery(GET_STOCK_MOMENTS, {
    variables: {
      symbol: symbol.toUpperCase(),
      range: chartRange,
    },
    skip: !symbol,
    errorPolicy: 'all',
    fetchPolicy: 'cache-and-network',
  });

  // Transform GraphQL response
  const moments: StockMomentType[] = useMemo(() => {
    if (!data?.stockMoments) return [];
    return data.stockMoments.map((m: any) => ({
      id: m.id,
      symbol: m.symbol,
      timestamp: m.timestamp,
      category: m.category,
      title: m.title,
      quickSummary: m.quickSummary,
      deepSummary: m.deepSummary,
    }));
  }, [data]);

  // Render components
  return (
    <View>
      <ChartWithMoments
        priceSeries={priceSeries}
        moments={moments}
        onMomentChange={...}
        onMomentLongPress={...}
      />
      <MomentStoryPlayer
        visible={storyVisible}
        symbol={symbol}
        moments={moments}
        speakFn={(text, moment) => playWealthOracle(text, symbol, moment)}
        stopFn={stopWealthOracle}
      />
    </View>
  );
};
```

---

## 🎨 Frontend: UI Components

### 1. ChartWithMoments Component

**File**: `mobile/src/components/charts/ChartWithMoments.tsx`

**Features:**
- Renders line chart with price data
- Shows moment dots on chart at correct timestamps
- Handles drag gestures to explore moments
- Long-press on dot → opens Story Mode
- Haptic feedback when passing over moments

**Key Code:**
```typescript
export type StockMoment = {
  id: string;
  symbol: string;
  timestamp: string;
  category: MomentCategory;
  title: string;
  quickSummary: string;
  deepSummary: string;
};

const ChartWithMoments: React.FC<ChartWithMomentsProps> = ({
  priceSeries,
  moments,
  onMomentChange,
  activeMomentId,
  onMomentLongPress,
}) => {
  // Renders SVG chart with moments as dots
  // Handles PanResponder for drag/long-press
  // Highlights active moment
};
```

### 2. MomentStoryPlayer Component

**File**: `mobile/src/components/charts/MomentStoryPlayer.tsx`

**Features:**
- Cinematic story player modal
- Auto-scrolls through moments
- Voice narration (TTS or expo-speech)
- Play/Pause/Next/Previous controls
- Intro slide (optional)
- Analytics tracking

**Key Code:**
```typescript
const MomentStoryPlayer: React.FC<MomentStoryPlayerProps> = ({
  visible,
  symbol,
  moments,
  initialIndex,
  enableIntro,
  speakFn,  // Custom TTS (Wealth Oracle)
  stopFn,
  onAnalyticsEvent,
}) => {
  // Uses FlatList for horizontal scrolling
  // Auto-plays voice narration
  // Tracks listened moments
  // Fires analytics events
};
```

---

## 🗣️ Voice Narration (TTS)

### File: `mobile/src/services/wealthOracleTTS.ts`

```typescript
export async function playWealthOracle(
  text: string,
  symbol: string,
  moment: StockMoment,
): Promise<void> {
  // Try TTS microservice first
  try {
    const res = await fetch(`${TTS_API_BASE_URL}/tts`, {
      method: "POST",
      body: JSON.stringify({ text, voice: "wealth_oracle_v1", ... }),
    });
    // Play audio from service
  } catch (error) {
    // Fallback to expo-speech
    Speech.speak(text, wealthOracleVoiceOptions);
  }
}
```

**Flow:**
1. Try custom TTS microservice (FastAPI + gTTS)
2. If fails → fallback to `expo-speech`
3. Uses `deep_summary` from AI-generated moment

---

## 🔄 Complete Workflow

### 1. **Generation Phase** (Backend Worker)
```python
# stock_moment_worker.py
job = RawMomentJob(
    symbol="AAPL",
    timestamp=datetime.now(),
    price_context=PriceContext(...),
    events=[Event(...), ...]
)

# Call OpenAI
moment_data = call_llm_for_moment(job)

# Save to DB
StockMoment.objects.create(
    symbol="AAPL",
    title=moment_data["title"],
    quick_summary=moment_data["quick_summary"],
    deep_summary=moment_data["deep_summary"],
    category=moment_data["category"],
    importance_score=moment_data["importance_score"],
)
```

### 2. **API Phase** (GraphQL)
```graphql
query {
  stockMoments(symbol: "AAPL", range: ONE_MONTH) {
    id
    title
    quickSummary
    deepSummary
    category
  }
}
```

### 3. **UI Phase** (React Native)
```typescript
// Fetch moments
const { data } = useQuery(GET_STOCK_MOMENTS, { variables: { symbol: "AAPL", range: "ONE_MONTH" } });

// Display on chart
<ChartWithMoments moments={moments} priceSeries={priceData} />

// Play story
<MomentStoryPlayer moments={moments} speakFn={playWealthOracle} />
```

---

## 🎯 Key Features

1. **AI-Powered**: Uses OpenAI GPT-4o-mini to generate moments
2. **Structured Data**: JSON response with title, summaries, category
3. **Filtered**: Only saves moments with `importance_score > 0.05`
4. **Categorized**: EARNINGS, NEWS, INSIDER, MACRO, SENTIMENT, OTHER
5. **Voice Narration**: TTS service with expo-speech fallback
6. **Interactive Chart**: Drag to explore, long-press to play story
7. **Cinematic Player**: Auto-scroll, voice, analytics

---

## 📝 Summary

**Yes, we are using GenAI!** The flow is:

1. **Backend Worker** (`stock_moment_worker.py`) → Calls **OpenAI GPT-4o-mini**
2. **Django Model** (`StockMoment`) → Stores AI-generated data
3. **GraphQL API** (`queries.py`) → Serves moments to frontend
4. **React Native UI** → Displays moments on chart + story player
5. **TTS Service** → Narrates AI-generated `deep_summary`

The AI generates:
- `title`: Short headline
- `quick_summary`: Brief explanation (for chart tooltips)
- `deep_summary`: Detailed explanation (for voice narration)
- `category`: Type of moment
- `importance_score`: How significant (0.0 - 1.0)

