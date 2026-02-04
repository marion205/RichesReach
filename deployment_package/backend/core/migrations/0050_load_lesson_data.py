# Load initial 6 lessons (from former MOCK_LESSONS in lesson_api.py)

from django.db import migrations


def load_lessons(apps, schema_editor):
    Lesson = apps.get_model("core", "Lesson")
    lessons = [
        {
            "id": "1",
            "title": "What is a Stock?",
            "description": "Learn the fundamentals of stocks and how they work",
            "duration_minutes": 2,
            "difficulty": "beginner",
            "category": "basics",
            "concepts": ["stocks", "equity", "ownership"],
            "content": "A stock represents ownership in a company. When you buy a stock, you're buying a small piece of that company. If the company does well, your stock value increases. If it does poorly, your stock value decreases. Stocks are traded on exchanges like the New York Stock Exchange (NYSE) or NASDAQ.",
            "key_takeaways": [
                "Stocks represent ownership in a company",
                "Stock prices fluctuate based on company performance",
                "Diversification helps reduce risk",
            ],
            "order": 1,
        },
        {
            "id": "2",
            "title": "Understanding Market Volatility",
            "description": "Why markets go up and down, and what it means for you",
            "duration_minutes": 3,
            "difficulty": "beginner",
            "category": "basics",
            "concepts": ["volatility", "market cycles"],
            "content": "Market volatility refers to how much stock prices fluctuate. High volatility means prices swing widely; low volatility means prices are more stable. Volatility is normal and expected in investing. It's driven by factors like economic news, company earnings, and investor sentiment. For long-term investors, volatility is less concerning than for short-term traders.",
            "key_takeaways": [
                "Volatility is normal in investing",
                "Long-term investors can ride out volatility",
                "Don't make decisions based on daily price swings",
            ],
            "order": 2,
        },
        {
            "id": "3",
            "title": "Building Your First Portfolio",
            "description": "Step-by-step guide to creating a diversified portfolio",
            "duration_minutes": 5,
            "difficulty": "intermediate",
            "category": "portfolio",
            "concepts": ["diversification", "asset allocation"],
            "content": "A diversified portfolio spreads your investments across different assets, sectors, and geographic regions. This reduces risk because if one investment performs poorly, others may perform well. A good starting portfolio might include: 60% stocks, 30% bonds, and 10% cash or alternatives. As you get older or your goals change, you might shift to more conservative investments.",
            "key_takeaways": [
                "Diversification reduces risk",
                "Asset allocation depends on your goals and timeline",
                "Rebalance your portfolio periodically",
            ],
            "order": 3,
        },
        {
            "id": "4",
            "title": "Risk vs. Reward",
            "description": "Understanding the relationship between risk and potential returns",
            "duration_minutes": 4,
            "difficulty": "intermediate",
            "category": "risk",
            "concepts": ["risk", "returns", "correlation"],
            "content": "In investing, there's a fundamental relationship: higher potential returns usually come with higher risk. Stocks have historically provided higher returns than bonds, but with more volatility. Bonds are generally safer but offer lower returns. Your risk tolerance depends on your age, financial situation, and goals. Younger investors can typically take more risk because they have time to recover from losses.",
            "key_takeaways": [
                "Higher returns usually mean higher risk",
                "Your risk tolerance depends on your situation",
                "Diversification helps balance risk and reward",
            ],
            "order": 4,
        },
        {
            "id": "5",
            "title": "Introduction to Bonds",
            "description": "What bonds are and how they work",
            "duration_minutes": 3,
            "difficulty": "beginner",
            "category": "bonds",
            "concepts": ["bonds", "fixed income", "yield"],
            "content": "A bond is essentially a loan you make to a company or government. In return, they pay you interest over time and return your principal when the bond matures. Bonds are generally less risky than stocks but offer lower potential returns. They're a good way to balance risk in your portfolio. Government bonds are the safest, while corporate bonds offer higher yields but more risk.",
            "key_takeaways": [
                "Bonds are loans to companies or governments",
                "Bonds provide steady income through interest payments",
                "Bonds are generally safer but offer lower returns than stocks",
            ],
            "order": 5,
        },
        {
            "id": "6",
            "title": "Tax-Efficient Investing",
            "description": "How to minimize taxes on your investments",
            "duration_minutes": 4,
            "difficulty": "intermediate",
            "category": "tax",
            "concepts": ["tax", "capital gains", "tax-advantaged accounts"],
            "content": "Tax-efficient investing means structuring your investments to minimize taxes. Key strategies include: using tax-advantaged accounts (401k, IRA), holding investments long-term to qualify for lower capital gains rates, and tax-loss harvesting (selling losing investments to offset gains). Understanding tax implications can significantly improve your after-tax returns over time.",
            "key_takeaways": [
                "Use tax-advantaged accounts when possible",
                "Long-term investments get better tax treatment",
                "Tax-loss harvesting can offset gains",
            ],
            "order": 6,
        },
    ]
    for data in lessons:
        Lesson.objects.update_or_create(
            id=data["id"],
            defaults={
                "title": data["title"],
                "description": data["description"],
                "duration_minutes": data["duration_minutes"],
                "difficulty": data["difficulty"],
                "category": data["category"],
                "concepts": data["concepts"],
                "content": data["content"],
                "key_takeaways": data["key_takeaways"],
                "order": data["order"],
            },
        )


def unload_lessons(apps, schema_editor):
    Lesson = apps.get_model("core", "Lesson")
    Lesson.objects.filter(id__in=["1", "2", "3", "4", "5", "6"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0049_lesson_model"),
    ]

    operations = [
        migrations.RunPython(load_lessons, unload_lessons),
    ]
