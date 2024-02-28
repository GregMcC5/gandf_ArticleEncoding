
# Using U-M GPT Toolkit to Apply Level-2, Article-Level Encoding on Text-Class Digital Collections

Gregory McCollum (gregmcc@umich.edu), February 2024




## Summary

This repository contains the scripts utilized by Gregory McCollum and Jackson Huang on a pilot project conducted during their time at the University of Michigan Library experimenting with using the U-M GPT Toolkit to develop a workflow for applying level-2 (article level) encoding to the text digital collecitons.

Specifically, this project utilized U-M Libray's [Garden and Forest](https://quod.lib.umich.edu/g/gandf/) collection of horticulture and botany journals. This collection currently has no encoded information on the articles within the journals, only provided access to the journal's pages. This project attempted to use a large langugage model to extract article information from the OCR of the Tables of Content of the journals held in this collection, and allow users to browse specific articles in each journal.

A more robust description of this project is available [here](https://docs.google.com/document/d/1EnHUxZ7e-XrN34WkSmk2p6Y8WQoveXNg0EuSK6sk9eM/edit?usp=sharing). UM Library employees can access further documentation [here](https://mlit.atlassian.net/l/cp/1vi2UDmN).


## Inventory

- *prompt_test.txt* - This file was used for notetakes during the process of refining our prompt. In here are three Tables of Content OCR from the Garden and Forest Collection, a series of prompts, and the outputs from the OpenAI ChatGPT web tool when given a prompt and each of the sample OCR. Multiple iterations of this testing occurred and you'll find notes mentioning the changes to our process.

- *api_calls.py* - For each item in *gandf.xml* (not included in this repository), this script extracts the OCR text of the volume's Table of Contents page, and calls the LLM API with this OCR and our finalized prompt. The outputs are stored as a JSON file *api_outputs.json*, associating the API output with each volume's DLXS ID as key-value pairs.

- *env* - This file contains the environment variables loaded by the *api_calls.py* script. The utilized version includes the API keys and Organizational code that are absent here.

- *api_outputs.json* - The outputs from our calls to the OpenAI API live here. The keys in this JSON are the DLXS ids for all of Garden and Forest; the values are the output from the API. Specifically, the values are a list of dictionaries, each one representing an "entry" or line in that volume's Table of Contents, with an Article Title, Author (if available), a Page Number, and a Heading (the section under which the article fell in the journal; this piece of data was not used)

- *gandf_data/ajq0745.0001.004.xml* - This is the item xml file which was used as the primary example for this pilot project. This article level information from *api_outputs.json* were spliced into this file.

- *splice_xml.py* - This script takes an identified item ID and restructures it with the article-level data from *api_outputs.json*. First it develops a list of DIV tags, one for each article from OpenAI outputs with article title, author, and page number information. It then loops through this list and  appends the existing P (page, containing OCR) tags for each page associated with each article under its corresponding DIV tag. 

	Another loop through this list of DIV tags occurs again, with the script trimming the OCR for instances in which the same page is featured for multiple articles (pages with multiple articles on them). This trimming occurs by checking for occurrences of the article title on the page, both with exact-string matching and fuzzy-matching.
    
    Some special handling of the Table of Contents and Front Matters occurs before the whole list of DIV tags is wrapped in a BODY tag and appended under the original item XML file's TEXT tag. The new file is then written as new_{item_id}.xml


## Notes

This workflow was constructed with a single item (ajq0745.0001.004) in mind. Multiple issues arose when attempting to apply the *splice_xml.py* script to other items whose article-level information was extracted. 

More information on the this project can be found [here](https://mlit.atlassian.net/l/cp/1vi2UDmN).

Gregory McCollum can also be contacted at gregmcc@uchicago.edu.
