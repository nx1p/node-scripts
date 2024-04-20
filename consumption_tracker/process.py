import sqlite3
from pydantic import BaseModel, Field, ValidationError
from rich.pretty import pprint
from rich.progress import Progress, BarColumn, SpinnerColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from phi.assistant import Assistant
from phi.llm.groq import Groq
#from phi.llm.fireworks import Fireworks
from phi.llm.anthropic import Claude


class SubstanceConsumption(BaseModel):
    substance: str = Field(..., description="Name of the substance consumed.")
    dosage: float = Field(..., description="Dosage of the substance.")
    dosage_unit: str = Field(..., description="Unit of the dosage (mg, ml, etc.).")
    route_of_administration: str = Field(..., description="Route of administration (e.g., oral, sublingual). If unknown, LEAVE EMPTY!!")
    timestamp: str = Field(..., description="Timestamp of when the substance was consumed. (Leave empty.)")

substance_names = [
    "Caffeine",
    "Alcohol",
    "Cannabis",
    "Amphetamine",
    "Dexamphetamine",
    "Modafinil",
    "LSD",
    "Ketamine",
    "Methamphetamine",
    "MDMA",
    "Diazepam",
]

extra_instructions = [
    f"When extracting the substance name, please use one of the following spellings if applicable: {', '.join(substance_names)}",
    "If the substance is not in the list above, use the most common spelling for that substance.",
    "If the route of administration is not specified, leave it empty.",
]

substance_assistant = Assistant(
    llm=Groq(model="llama3-70b-8192"),
    #llm=Fireworks(model="accounts/fireworks/models/llama-v3-8b-instruct", temperature=0.1),
    #llm=Claude(model="claude-3-haiku-20240307"),
    description="You help extract substance consumption data from natural language messages.",
    extra_instructions=extra_instructions,
    debug_mode=False,
    output_model=SubstanceConsumption,
)

def get_misc_channel_messages():
    conn = sqlite3.connect('discord_data.db')
    c = conn.cursor()
    c.execute("SELECT m.content, m.timestamp FROM messages m JOIN channels c ON m.channel_id = c.id WHERE c.name = 'misc'")
    messages = c.fetchall()
    conn.close()
    return messages

def process_message(message, retry_count=5):
    for attempt in range(retry_count):
        try:
            data = substance_assistant.run(message)
            return data
        except (ValidationError, Exception) as e:
            if attempt < retry_count - 1:
                print(f"Error processing message (attempt {attempt + 1}): {message}")
                print(f"Error: {str(e)}")
            else:
                raise

def store_substance_consumption(data):
    conn = sqlite3.connect('substance_consumption-llamav3-70b.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS consumption
                 (substance TEXT, dosage REAL, dosage_unit TEXT, route_of_administration TEXT, timestamp TEXT)''')
    c.execute("INSERT INTO consumption VALUES (?, ?, ?, ?, ?)",
              (data.substance, data.dosage, data.dosage_unit, data.route_of_administration, data.timestamp))
    conn.commit()
    conn.close()

def main():
    messages = get_misc_channel_messages()
    total_messages = len(messages)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("Processed: {task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("[cyan]Processing messages...", total=total_messages)

        for message, timestamp in messages:
            try:
                data = process_message(message)
                data.timestamp = timestamp
                pprint(data)  # Pretty-print the extracted data for debugging
                store_substance_consumption(data)
            except (ValidationError, Exception) as e:
                print(f"Skipping message due to error: {message}")
                print(f"Error: {str(e)}")

            progress.update(task, advance=1)

if __name__ == "__main__":
    main()
