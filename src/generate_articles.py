import os
import boto3
from dotenv import load_dotenv

load_dotenv()

# Simulated article data — in a real app these would come from a database or API
ARTICLES = [
    {
        "id": "article_001",
        "title": "The Rise of Renewable Energy",
        "content": (
            "Renewable energy sources such as solar, wind, and hydroelectric power are transforming "
            "the global energy landscape. Over the past decade, the cost of solar panels has dropped "
            "by over 90%, making clean energy accessible to more countries than ever before. "
            "Governments worldwide are setting ambitious targets to phase out fossil fuels and reach "
            "net-zero carbon emissions by 2050. Wind farms, both onshore and offshore, are expanding "
            "rapidly, with offshore installations taking advantage of stronger, more consistent winds. "
            "Energy storage technology, particularly lithium-ion batteries, is solving the intermittency "
            "problem that once limited renewables. The transition to clean energy is not just an "
            "environmental imperative — it is increasingly an economic one."
        ),
    },
    {
        "id": "article_002",
        "title": "How Large Language Models Work",
        "content": (
            "Large language models (LLMs) are neural networks trained on vast amounts of text data. "
            "They learn to predict the next token in a sequence, which — at scale — produces systems "
            "capable of reasoning, summarization, and code generation. The transformer architecture, "
            "introduced in the 2017 paper 'Attention Is All You Need', is the foundation of modern LLMs. "
            "Attention mechanisms allow the model to weigh the relevance of every word in a sentence "
            "relative to every other word, capturing long-range dependencies that earlier models missed. "
            "Training requires massive compute clusters running for weeks or months. Fine-tuning and "
            "reinforcement learning from human feedback (RLHF) align the raw model to be helpful, "
            "harmless, and honest. LLMs like GPT-4 and Claude are now embedded in products used by "
            "hundreds of millions of people daily."
        ),
    },
    {
        "id": "article_003",
        "title": "The History of the Internet",
        "content": (
            "The internet began as ARPANET, a US Department of Defense project in the late 1960s designed "
            "to create a decentralized communication network that could survive a nuclear attack. Early "
            "adoption was limited to universities and research institutions. The invention of the World "
            "Wide Web by Tim Berners-Lee in 1989 democratized access, introducing hyperlinks and browsers "
            "that made navigation intuitive. The 1990s saw explosive commercial growth, culminating in the "
            "dot-com bubble and bust. Broadband replaced dial-up in the 2000s, enabling video streaming "
            "and social media. Mobile internet, driven by smartphones, made connectivity ubiquitous. "
            "Today, over five billion people are online, and the internet underpins nearly every sector "
            "of the global economy."
        ),
    },
    {
        "id": "article_004",
        "title": "Advances in CRISPR Gene Editing",
        "content": (
            "CRISPR-Cas9 is a molecular tool that allows scientists to edit DNA with unprecedented "
            "precision. Derived from a bacterial immune system, CRISPR uses a guide RNA to direct the "
            "Cas9 enzyme to a specific location in the genome, where it makes a targeted cut. Researchers "
            "can then disable a gene or insert new genetic material. Since its adaptation for human cells "
            "in 2012, CRISPR has accelerated research into genetic diseases, cancer therapies, and crop "
            "improvement. Clinical trials are underway for sickle cell disease and beta-thalassemia, with "
            "early results showing patients achieving functional cures. Ethical debates around germline "
            "editing — changes that would be inherited by future generations — remain active and unresolved. "
            "CRISPR represents both enormous promise and significant responsibility."
        ),
    },
    {
        "id": "article_005",
        "title": "The Economics of Remote Work",
        "content": (
            "The COVID-19 pandemic forced a global experiment in remote work, accelerating a shift that "
            "was already underway. Knowledge workers discovered that many tasks previously assumed to "
            "require in-person presence could be done effectively from home. Companies reported mixed "
            "results: some saw productivity gains, others struggled with collaboration and culture. "
            "Real estate markets shifted dramatically as workers relocated from expensive cities to "
            "lower-cost regions, enabled by geographic flexibility. Employers began competing for talent "
            "on a global scale, compressing wages in high-cost markets while raising them elsewhere. "
            "Hybrid work — a mix of in-office and remote days — emerged as the dominant model for large "
            "organizations. The long-term economic effects, from commercial real estate to urban tax bases, "
            "are still unfolding."
        ),
    },
]


def upload_articles_to_s3():
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )
    bucket = os.getenv("S3_BUCKET_NAME")

    for article in ARTICLES:
        filename = f"{article['id']}.txt"
        body = f"Title: {article['title']}\n\n{article['content']}"

        s3.put_object(
            Bucket=bucket,
            Key=f"articles/{filename}",
            Body=body,
            ContentType="text/plain",
        )
        print(f"Uploaded: articles/{filename}")

    print(f"\nDone. {len(ARTICLES)} articles uploaded to s3://{bucket}/articles/")


if __name__ == "__main__":
    upload_articles_to_s3()
