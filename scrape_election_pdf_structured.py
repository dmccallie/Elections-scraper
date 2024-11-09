import os
from pathlib import Path
from typing import List, Optional
from openai import OpenAI


import pdfplumber
import pandas as pd
import json

from extraction_models import Contest, Choice, Summary, ElectionData

def extract_election_data(batch_num:int,  text:str, api_key: str) -> Optional[ElectionData]:

    prompt = (
        f"""
        Extract all the ElectionData information from the following text:
        Text:\n{text}\n\n
        """
    )    
    client = OpenAI(api_key=api_key)

    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=prompt,
    #     max_tokens=8000)
    
    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06", 
        messages=[
            {"role": "system", "content": "You are a helpful assistant for extracting structured data from a PDF."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4000,  # adjust if needed
        temperature=0.2,  # adjust to control creativity
        response_format=ElectionData
    )

    # res will be a pydantic ElectionData object    
    res = response.choices[0].message.parsed
    print(f"batch number: {batch_num} finish reason:", response.choices[0].finish_reason)
    
    # Clean the content by removing unwanted characters and formatting
    # if res is not None and "```json" in res:
    #     cleaned_res = res.strip().strip("```json").strip("```").strip("'").strip("\n")
    
    # dump the batch of ElectionData to a json file
    if res is not None:
        # with open(f"election_data_batch_{batch_num}.json", "w") as f:
        #     f.write(res.model_dump_json())

        # json_data = res.model_dump_json() # json.loads(cleaned_res)
        return res
    
    return None


# when processing batches, a Contest may get split across two batches, so we need to merge them
# in theory, no Choices will ever be split across batches, but we can test before merging them too

def merge_contests(master_contests: List[Contest], new_contests: List[Contest]) -> List[Contest]:
    # Create a dictionary for easy lookup of contests by their name in the master list
    master_dict = {contest.name: contest for contest in master_contests}

    for new_contest in new_contests:
        if new_contest.name in master_dict:
            # Contest already exists, merge the choices
            master_contest = master_dict[new_contest.name]
            merge_choices(master_contest, new_contest.choices)
        else:
            # New contest, add it to the master list
            master_contests.append(new_contest)
    
    return master_contests


# make sure we don't duplicate a choice - should never happen?

def merge_choices(master_contest: Contest, new_choices: List[Choice]):
    master_choices:List[Choice] = master_contest.choices
    # Create a dictionary for easy lookup of choices by their name in the master list
    master_choice_dict = {choice.name: choice for choice in master_choices}

    for new_choice in new_choices:
        if new_choice.name in master_choice_dict:
            # Choice already exists, you can choose how to handle duplicates, for example:
            # sum the votes or ignore the new choice
            # master_choice = master_choice_dict[new_choice.name]
            # master_choice.vote_in_center += new_choice.vote_in_center
            # master_choice.vote_by_mail += new_choice.vote_by_mail
            # master_choice.vote_total += new_choice.vote_total
            print(f"OOPS - duplicate choice name found in Contest:{master_contest.name} Choice: {new_choice.name}")
        else:
            # New choice, add it to the master list of choices
            print(f"Merging in new choice: {new_choice.name} to Contest: {master_contest.name}")
            master_choices.append(new_choice)

def merge_summary(master_summaries: List[Summary], new_summaries: List[Summary]) -> List[Summary]:
    # Create a dictionary for easy lookup of summaries by their contest name in the master list
    master_dict = {summary.contest: summary for summary in master_summaries}

    for new_summary in new_summaries:
        if new_summary.contest in master_dict:
            print("OOPS - duplicate summary found for contest:", new_summary.contest)
            # Summary already exists, add in the new data
            # this shouldn't happen, but if it does, we can sum the values
            master_summary = master_dict[new_summary.contest]
            master_summary.undervotes_in_center += new_summary.undervotes_in_center
            master_summary.undervotes_by_mail += new_summary.undervotes_by_mail
            master_summary.undervotes_total += new_summary.undervotes_total
            master_summary.overvotes_in_center += new_summary.overvotes_in_center
            master_summary.overvotes_by_mail += new_summary.overvotes_by_mail
            master_summary.overvotes_total += new_summary.overvotes_total
            master_summary.unresolved_write_ins_in_center += new_summary.unresolved_write_ins_in_center
            master_summary.unresolved_write_ins_by_mail += new_summary.unresolved_write_ins_by_mail
            master_summary.unresolved_write_ins_total += new_summary.unresolved_write_ins_total
        else:
            # New summary, add it to the master list
            # print(f"Merging in new summary: {new_summary.contest}")
            master_summaries.append(new_summary)
    
    return master_summaries


# def save_results(json_data: str):
#     contests = []
#     summaries = []

#     # Process and save the results using pydantic models
#     # json_data = json.loads(json_data)

#     for contest_data in json_data["contests"]:
#         contest = Contest(**contest_data)
#         contests.append(contest)

#     for contest_data in json_data["summary"]:

#         summary = Summary(
#             contest=contest.name,
#             undervotes_in_center=contest_data["undervotes_in_center"],
#             undervotes_by_mail=contest_data["undervotes_by_mail"],
#             undervotes_total=contest_data["undervotes_total"],
#             overvotes_in_center=contest_data["overvotes_in_center"],
#             overvotes_by_mail=contest_data["overvotes_by_mail"],
#             overvotes_total=contest_data["overvotes_total"],
#             unqualified_write_ins_in_center=contest_data["unqualified_write_ins_in_center"],
#             unqualified_write_ins_by_mail=contest_data["unqualified_write_ins_by_mail"],
#             unqualified_write_ins_total=contest_data["unqualified_write_ins_total"],
#         )
#         summaries.append(summary)

    # I couldn't get this to work with panda extracting the model names and values automatically
    #  so I am listing the fields manually
    # data = []
    # for contest in contests: # list
    #     for choice in contest.choices:
    #         print(contest.name, choice.name, choice.party, choice.vote_in_center, choice.vote_by_mail, choice.vote_total)
    #         data.append([contest.name, choice.name, choice.party, choice.vote_in_center, choice.vote_by_mail, choice.vote_total])
    
    # contests_df = pd.DataFrame(data, columns=["contest", "name", "party", "vote_in_center", "vote_by_mail", "vote_total"])


    # # Convert to DataFrame and save to CSV
    # # contests_df = pd.DataFrame([contest.model_dump() for contest in contests]) # this doesn't work right
    # summaries_df = pd.DataFrame([summary.model_dump() for summary in summaries])

    # contests_df.to_csv("contests.csv", index=False)
    # summaries_df.to_csv("summaries.csv", index=False)


# define a generator to get the next batch of pages from the PDF
def get_next_batch(pdf_path: Path, pages_per_batch: int):
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(0, len(pdf.pages), pages_per_batch):
            text = ""
            for page in pdf.pages[i:i + pages_per_batch]:
                print(f"Processing page {page.page_number}")
                text += page.extract_text()
            yield text


def main(pdf_path: Path, api_key: str):

    # batch process the PDF and merge the new batch into master results
    # assumes that contests are always presented in a labelled table, even if the Choices are split across pages!!

    pages_per_batch = 8
    master_election_data: ElectionData = ElectionData(contests=[], summary=[])
    master_summaries = []

    for batch_num, next_batch in enumerate(get_next_batch(pdf_path, pages_per_batch)):

        words = len(next_batch.split())
        print(f"\nStart processing batch number: {batch_num} with length {words} words") # with text = {next_batch}")
        batch_election_data = extract_election_data(batch_num, next_batch, api_key)
        print("batch election data:", batch_election_data)
        if batch_election_data is not None:
            _ = merge_contests(master_election_data.contests, batch_election_data.contests)
            _ = merge_summary(master_election_data.summary, batch_election_data.summary)
        else:
            print(f"UNEXPECTED - Batch number: {batch_num} returned No Data!")

        print(f"Finished batch number: {batch_num}") # returns with electionData: {batch_election_data}")

    print("Finished processing all batches")
    if master_election_data is not None:
        with open(f"election_data_cumulative.json", "w") as f:
            f.write(master_election_data.model_dump_json())


if __name__ == "__main__":
    
    from dotenv import load_dotenv
    load_dotenv() # make sure our environment variables are loaded

    pdf_path = Path("./Fall-2024-first-post-report.pdf")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key not found")
    main(pdf_path, api_key)