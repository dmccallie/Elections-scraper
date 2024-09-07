import os
from pathlib import Path
from openai import OpenAI


import pdfplumber
import pandas as pd
import json

from extraction_models import Contest, Summary

def extract_election_data(pdf_path: Path, api_key: str):

    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        # for page in pdf.pages:
        #     text += page.extract_text()
        text = pdf.pages[0].extract_text() # 
        text += pdf.pages[1].extract_text() # 
        # text += pdf.pages[2].extract_text() # 
        # text += pdf.pages[3].extract_text()

    # Use the OpenAI API to parse the PDF text
    prompt = (
        f"""
        Extract the following information from the text:
        
        1) Extract contests and their choices.
            Note that contest's name is in upper case, and is on a text line like this: 'PRESIDENT - Democratic - Vote for One',
              but the actual contest name is text and party without the " - Vote for XXX" instruction.
            Some contests will have party information, and some will not.
        
            Each contest has a list of choices.
            Each choice has the following fields: name, party, vote_in_center, vote_by_mail, and vote_total.
            Note that a choice_name may be "Yes" or "No" for some contests.
        
        2) Extract a summary that includes the contest's name,
             undervotes_in_center, undervotes_by_mail, undervotes_total,
             overvotes_in_center, overvotes_by_mail, overvotes_total,
             unqualified_write_ins_in_center, unqualified_write_ins_by_mail, unqualified_write_ins_total.
        
        Text:\n{text}\n\n
        Return the answer as structured JSON.
        """
    )
    client = OpenAI(api_key=api_key)

    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=prompt,
    #     max_tokens=8000)
    
    response = client.chat.completions.create(
        model="gpt-4o",  # or use "gpt-4" if you have access
        messages=[
            {"role": "system", "content": "You are a helpful assistant for extracting structured data from a PDF."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4000,  # adjust if needed
        temperature=0.2  # adjust to control creativity
    )

    #return response.choices[0].text
    res = response.choices[0].message.content
    
    # Clean the content by removing unwanted characters and formatting
    if res is not None and "```json" in res:
        cleaned_res = res.strip().strip("```json").strip("```").strip("'").strip("\n")
    
    # dump the cleaned response to a json file
    with open("cleaned_res.json", "w") as f:
        f.write(cleaned_res)

    json_data = json.loads(cleaned_res)
    return json_data


def save_results(json_data: str):
    contests = []
    summaries = []

    # Process and save the results using pydantic models
    # json_data = json.loads(json_data)

    for contest_data in json_data["contests"]:
        contest = Contest(**contest_data)
        contests.append(contest)

    for contest_data in json_data["summary"]:

        summary = Summary(
            contest=contest.name,
            undervotes_in_center=contest_data["undervotes_in_center"],
            undervotes_by_mail=contest_data["undervotes_by_mail"],
            undervotes_total=contest_data["undervotes_total"],
            overvotes_in_center=contest_data["overvotes_in_center"],
            overvotes_by_mail=contest_data["overvotes_by_mail"],
            overvotes_total=contest_data["overvotes_total"],
            unqualified_write_ins_in_center=contest_data["unqualified_write_ins_in_center"],
            unqualified_write_ins_by_mail=contest_data["unqualified_write_ins_by_mail"],
            unqualified_write_ins_total=contest_data["unqualified_write_ins_total"],
        )
        summaries.append(summary)

    # I couldn't get this to work with panda extracting the model names and values automatically
    #  so I am listing the fields manually
    data = []
    for contest in contests: # list
        for choice in contest.choices:
            print(contest.name, choice.name, choice.party, choice.vote_in_center, choice.vote_by_mail, choice.vote_total)
            data.append([contest.name, choice.name, choice.party, choice.vote_in_center, choice.vote_by_mail, choice.vote_total])
    
    contests_df = pd.DataFrame(data, columns=["contest", "name", "party", "vote_in_center", "vote_by_mail", "vote_total"])


    # Convert to DataFrame and save to CSV
    # contests_df = pd.DataFrame([contest.model_dump() for contest in contests]) # this doesn't work right
    summaries_df = pd.DataFrame([summary.model_dump() for summary in summaries])

    contests_df.to_csv("contests.csv", index=False)
    summaries_df.to_csv("summaries.csv", index=False)


def main(pdf_path: Path, api_key: str):
    json_data = extract_election_data(pdf_path, api_key)
    save_results(json_data)


if __name__ == "__main__":
    pdf_path = Path("./test_results.pdf")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key not found")
    main(pdf_path, api_key)