import json
import os
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from openai import OpenAI
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

load_dotenv()

OUTPUT_DIR = Path("generated/reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# AI REPORT CONTENT GENERATION
# --------------------------------------------------

def generate_report_content(topic, context=""):

    if not context or not context.strip():
        raise ValueError(
            "No document context was provided for report generation."
        )

    print("\nGenerating grounded report...")
    
    # --------------------------------------------------
    # SPLIT RETRIEVED DOCUMENT INTO CHUNKS
    # --------------------------------------------------

    chunks = context.split(
        "\n\n--- DOCUMENT CHUNK ---\n\n"
    )

    chunks = [
        chunk.strip()
        for chunk in chunks
        if chunk.strip()
    ]

    print(
        f"Report generator received {len(chunks)} document chunks."
    )

    # --------------------------------------------------
    # BATCH DOCUMENT CHUNKS
    # --------------------------------------------------

    # Larger batches reduce the number of LLM calls while keeping prompts manageable.
    BATCH_SIZE = 16

    batches = [
        chunks[i:i + BATCH_SIZE]
        for i in range(0, len(chunks), BATCH_SIZE)
    ]

    print(
        f"Processing {len(batches)} document batches..."
    )

    # --------------------------------------------------
    # ANALYZE BATCHES IN PARALLEL
    # --------------------------------------------------

    # Keep this modest because the Groq account has a TPM limit.
    # Keep concurrency modest to avoid provider TPM spikes and local Ollama queuing.
    MAX_WORKERS = 2

    # Pre-allocate so results stay in document order even
    # though batches finish in different orders.
    batch_summaries = [None] * len(batches)

    def process_batch(index, batch):
        batch_context = "\n\n".join(batch)

        batch_prompt = f"""
You are analyzing SOURCE DOCUMENT MATERIAL for a report.

REQUESTED TOPIC:
{topic}

SOURCE DOCUMENT EXCERPTS:
{batch_context}

STRICT RULES:

1. Use ONLY the supplied source excerpts.
2. Do NOT use outside knowledge.
3. Do NOT invent facts.
4. Do NOT invent statistics, dates, organizations,
   technologies, examples, requirements, or conclusions.
5. If something is not present in the excerpts,
   do not mention it.
6. Preserve the terminology used by the source.
7. Extract factual information rather than generating
   a general explanation from your own knowledge.

Analyze these excerpts and produce a factual source summary.

Focus on:
- Important concepts
- Definitions
- Processes
- Requirements
- Important facts
- Examples explicitly present
- Relationships between concepts
- Important conclusions explicitly supported

Return plain text only.
"""

        try:
            summary = _call_llm(
                batch_prompt,
                parse_json=False
            )

            if not summary:
                raise ValueError("LLM returned an empty batch summary.")

            if len(summary) > 5000:
                summary = summary[:5000]

            return index, summary

        except Exception as e:
            print(f"Batch {index} failed: {e}")
            raise

    print(
        f"Processing {len(batches)} batches "
        f"with {MAX_WORKERS} parallel workers..."
    )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = [
            executor.submit(
                process_batch,
                index,
                batch
            )
            for index, batch in enumerate(batches, start=1)
        ]

        for future in as_completed(futures):

            index, summary = future.result()

            batch_summaries[index - 1] = summary

            print(
                f"Processed batch "
                f"{index}/{len(batches)}"
            )

    if any(summary is None for summary in batch_summaries):
        raise RuntimeError(
            "One or more document batches did not produce a summary."
        )

    # --------------------------------------------------
    # COMBINE SOURCE SUMMARIES
    # --------------------------------------------------

    combined_source = "\n\n".join(
        f"--- SOURCE BATCH {index} ---\n{summary}"
        for index, summary
        in enumerate(batch_summaries, start=1)
    )
    combined_source = combined_source[:24000]
    

    print(
        f"Combining {len(batch_summaries)} source summaries..."
    )

    # --------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------

    final_prompt = f"""
You are a document-grounded report generator.

REQUESTED TOPIC:
{topic}

The following material consists ONLY of summaries
created from the source document.

SOURCE MATERIAL:
{combined_source}

STRICT GROUNDING RULES:

1. The source material above is your ONLY factual source.
2. Do NOT use pretrained/general knowledge.
3. Do NOT add information that is not supported by
   the source material.
4. Do NOT invent statistics, dates, names,
   technologies, examples, organizations,
   requirements, or events.
5. Do NOT assume that the requested topic itself
   proves anything.
6. If the source does not contain enough information
   for a point, omit the point.
7. Preserve the terminology and meaning of the
   source material.
8. Combine information from different source batches
   when they discuss the same subject.
9. Do not claim that something is in the document
   unless it is supported by the source material.
10. The report must represent the supplied document,
    not a generic report about the topic.

Create a professional analytical report.

Return ONLY valid JSON using this structure:

{{
    "title": "Report title based on the source document",
    "executive_summary": "Summary of the information actually supported by the source document.",
    "sections": [
        {{
            "title": "Section title",
            "content": [
                "Source-supported finding.",
                "Source-supported finding.",
                "Source-supported finding."
            ]
        }}
    ],
    "conclusion": "Conclusion supported by the source document."
}}

REPORT REQUIREMENTS:

- Create 5-8 sections where the source material supports them.
- Each section should contain 2-5 factual points.
- Cover the major subjects actually present in the source.
- Avoid repeating the same information.
- Do not introduce external information.
- Do not add generic textbook explanations.
- Do not fabricate missing information.
- Do not use markdown.
- Return ONLY JSON.
"""

    print(
        "\nGenerating final grounded report..."
    )

    # --------------------------------------------------
    # IMPORTANT:
    # _call_llm() already performs the provider fallback.
    # --------------------------------------------------

    result = _call_llm(final_prompt)

    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    if isinstance(result, dict):
        return result

    return _parse_report_json(result)


def _call_llm(prompt, parse_json=True):
    """
    Report generation providers:
    1. Groq API key #2
    2. Ollama local model
    """

    # --------------------------------------------------
    # GROQ - KEY 2
    # --------------------------------------------------

    groq_key = os.getenv("GROQ_API_KEY_2")

    if groq_key:
        try:
            print("\nTrying Groq API key #2 for report generation...")

            client = OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1"
            )

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
            )

            content = response.choices[0].message.content

            if not content:
                raise ValueError("Groq returned an empty response.")

            print("Groq API key #2 selected.")

            return (
                _parse_report_json(content)
                if parse_json
                else content
            )

        except Exception as e:
            print(f"Groq API key #2 unavailable: {e}")

    # --------------------------------------------------
    # OLLAMA
    # --------------------------------------------------

    local_base_url = os.getenv(
        "LOCAL_LLM_BASE_URL",
        "http://localhost:11434/v1"
    )

    local_model = os.getenv(
        "LOCAL_LLM_MODEL",
        "qwen2.5:7b-instruct"
    )

    try:
        print(f"\nTrying Ollama local model: {local_model}")

        client = OpenAI(
            api_key=os.getenv("LOCAL_LLM_API_KEY", "ollama"),
            base_url=local_base_url
        )

        response = client.chat.completions.create(
            model=local_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("Ollama returned an empty response.")

        print(f"Ollama selected: {local_model}")

        return (
            _parse_report_json(content)
            if parse_json
            else content
        )

    except Exception as e:
        print(f"Ollama unavailable: {e}")

    raise RuntimeError(
        "Unable to generate report using Groq key #2 or Ollama."
    )

# --------------------------------------------------
# PARSE JSON
# --------------------------------------------------

def _parse_report_json(content):

    if not content:
        raise ValueError("LLM returned an empty response.")

    content = content.strip()

    # Remove markdown fences if present
    if "```json" in content:
        content = content.replace("```json", "")

    if "```" in content:
        content = content.replace("```", "")

    content = content.strip()

    # --------------------------------------------------
    # TRY DIRECT JSON
    # --------------------------------------------------

    try:
        data = json.loads(content)
    except json.JSONDecodeError:

        # --------------------------------------------------
        # EXTRACT JSON OBJECT FROM EXTRA TEXT
        # --------------------------------------------------

        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError(
                "LLM did not return valid JSON."
            )

        json_text = content[start:end + 1]

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid JSON returned by LLM: {error}"
            )

    # --------------------------------------------------
    # VALIDATE STRUCTURE
    # --------------------------------------------------

    required = [
        "title",
        "executive_summary",
        "sections",
        "conclusion",
    ]

    for key in required:

        if key not in data:
            raise ValueError(
                f"Report response missing '{key}'."
            )

    if not isinstance(data["sections"], list):
        raise ValueError(
            "'sections' must be a list."
        )

    return data

# --------------------------------------------------
# PDF HEADER / FOOTER
# --------------------------------------------------

def _add_page_number(canvas, doc):

    canvas.saveState()

    canvas.setFont("Helvetica", 8)

    canvas.drawCentredString(
        A4[0] / 2,
        0.4 * inch,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# --------------------------------------------------
# CREATE PDF REPORT
# --------------------------------------------------

def create_report(topic, report_data):

    report_id = uuid.uuid4().hex

    filename = f"{report_id}.pdf"

    output_path = OUTPUT_DIR / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=55,
        bottomMargin=55,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=25,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=25,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=35,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        spaceBefore=18,
        spaceAfter=10,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=16,
        spaceAfter=10,
    )

    summary_style = ParagraphStyle(
        "Summary",
        parent=body_style,
        fontSize=11,
        leading=17,
    )

    story = []

    # --------------------------------------------------
    # COVER
    # --------------------------------------------------

    story.append(Spacer(1, 1.2 * inch))

    story.append(
        Paragraph(
            report_data["title"],
            title_style
        )
    )

    story.append(
        Paragraph(
            f"Analytical Report<br/>{topic}",
            subtitle_style
        )
    )

    story.append(Spacer(1, 1.5 * inch))

    metadata = Table(
        [
            ["Generated by", "Enterprise Intelligence Platform"],
            ["Report Type", "AI-Generated Analytical Report"],
        ],
        colWidths=[1.5 * inch, 4.5 * inch],
    )

    metadata.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
            ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f3f4f6")),
            ("TEXTCOLOR", (1, 0), (1, -1), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    story.append(metadata)

    story.append(PageBreak())

    # --------------------------------------------------
    # EXECUTIVE SUMMARY
    # --------------------------------------------------

    story.append(
        Paragraph(
            "Executive Summary",
            heading_style
        )
    )

    story.append(
        Paragraph(
            report_data["executive_summary"],
            summary_style
        )
    )

    story.append(Spacer(1, 10))

    # --------------------------------------------------
    # SECTIONS
    # --------------------------------------------------

    for section in report_data["sections"]:

        story.append(
            Paragraph(
                section.get("title", "Section"),
                heading_style
            )
        )

        for paragraph in section.get("content", []):

            story.append(
                Paragraph(
                    str(paragraph),
                    body_style
                )
            )

    # --------------------------------------------------
    # CONCLUSION
    # --------------------------------------------------

    story.append(
        Paragraph(
            "Conclusion",
            heading_style
        )
    )

    story.append(
        Paragraph(
            report_data["conclusion"],
            body_style
        )
    )

    # --------------------------------------------------
    # BUILD
    # --------------------------------------------------

    doc.build(
        story,
        onFirstPage=_add_page_number,
        onLaterPages=_add_page_number,
    )

    return {
        "report_id": report_id,
        "filename": filename,
        "path": str(output_path),
    }
