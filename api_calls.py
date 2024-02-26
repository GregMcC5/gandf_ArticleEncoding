from dotenv import dotenv_values
import openai
import json
import os
import metadata_utils as mu

#three step workflow
    # This scirpt (make api calls)
    # check output, flag what needs to be manually reviewed
    # splice it into the xml pages (need individual volume level ones)

#this script is the worklfow for making ai api calls with the table of contents pages from the table of contents pages from gand
#outputs are stored like a cache; no repeating calls for those already with an output.

secrets = dotenv_values(".env")  

system_prompt = '''You are an assistant for librarians working with OCR text collections. Your task is to extract article titles, authors, and page numbers of a historic academic journal's Table of Contents related to horticulture. Provide this information in a JSON list of dictionaries with keys "Article Title," "Author" (if present, otherwise leave blank), "Page Number," "Heading." Page number data is required for each article dictionary. If no page number is in the OCR, insert one in the dictionary. Note that you might find typos or issues in the OCR. Keep in mind that the Table of Contents may contain typos, errors, or be messy. For articles listed with section headings in mostly all-caps like "EDITORIAL ARTICLES," "FOREIGN CORRESPONDENCE," or "CULTURAL DEPARTMENT," include the heading in the "Heading" key. Heading may also appear in a line to themself. If an article doesn't have a Heading with it, use the most recent previous one. Stop when you reach the "Illustrations" section or the end of the Table of Contents.'''

def make_call(ocr):
    return openai.ChatCompletion.create(
        api_key = secrets['OPENAI_API_KEY'],
        organization = secrets['OPENAI_organization'],
        api_base= secrets['openai_api_base'],
        api_type = secrets['openai_api_type'],
        api_version = secrets['API_VERSION'],
        engine = secrets['model'],
        messages = [{"role":"system","content":system_prompt},
                    {"role":"user","content":f"Here is the OCR: {ocr}"}],
        temperature=0,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)

def main():
    gandf = mu.read_xml("gandf.xml")
    outputs = mu.read_json("api_outputs.json")
    print(type(list(gandf.find_all("DLPSTEXTCLASS"))))
    i = 0
    for item in list(gandf.find_all("DLPSTEXTCLASS")):
        print(type(item))
        dlxs_id = item.find("IDNO").text
        print(dlxs_id)
        if dlxs_id.split(".")[-1] != "000" and dlxs_id not in outputs.keys():
            toc_page_ocr = [page.text for page in item.find_all("P") if page.find("PB")][2]
            if "table of contents".lower() in toc_page_ocr.lower() or "TABLE OF' CONTENTS" in toc_page_ocr:
                print("making call")
                output = make_call(toc_page_ocr)
                print(output)
                try:
                    outputs[dlxs_id] = json.loads(output['choices'][0]['message']['content'])
                except:
                    outputs[dlxs_id] = output['choices'][0]['message']['content']
                    os.system(f'"echo issue loading {dlxs_id} as JSON" > api_call_logs.txt')
                mu.write_json("api_outputs.json", outputs)
                print('wrote it')
                i += 1
                print(i)
                if i > 4:
                    break
            else:
                print("no toc")
                break

    print("done")

if __name__ == "__main__":
    main()


