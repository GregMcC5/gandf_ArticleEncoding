import metadata_utils as mu
import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def main():
    #------------
    #--Pilot ID--
    #------------
    ID = "AJQ0745.0001.004" #<--- Any ID can go here

    api_outputs = [val for key,val in mu.read_json("api_outputs.json").items() if key == ID][0]

    tree = ET.parse(f"gandf_data/{ID}.xml")
    root = tree.getroot()

    # tree = ET.parse(f"gandf.xml")
    # root = [x for x in tree.iter("DLPSTEXTCLASS") if x.find("HEADER").find("FILEDESC").find("PUBLICATIONSTMT").find("IDNO").text == ID][0]

    #------------------------------
    #--Adding GPT Content as DIVs--
    #------------------------------
    divs = []
    pages_covered = set()
    node_counter = 1
    for idx, entry in enumerate(api_outputs):
        page_end = api_outputs[idx+1]["Page Number"] if idx + 1 < len(api_outputs) and api_outputs[idx+1]["Page Number"] != entry["Page Number"] else None
        #div1
        div1 = ET.Element("DIV1", attrib={"NODE" : f"{ID}:{node_counter}"})
        node_counter += 1
        #bibl
        bibl = ET.Element("BIBL")
        div1.append(bibl)
        #info 
        if entry["Author"]:
            authorind = ET.Element("AUTHORIND")
            authorind.text = entry["Author"]
            bibl.append(authorind)

        title = ET.Element("TITLE")
        title.text = entry["Article Title"]
        bibl.append(title)

        vol = ET.Element("BIBLSCOPE", attrib={"TYPE":"vol"})
        vol.text = ID.split(".")[1].replace("0", "")
        bibl.append(vol)

        iss = ET.Element("BIBLSCOPE", attrib={"TYPE":"iss"})
        iss.text = ID.split(".")[-1].replace("0", "")
        bibl.append(iss)

        if page_end:
            pg = ET.Element("BIBLSCOPE", attrib={"TYPE":"pg"})
            pg.text = entry["Page Number"]+"-"+page_end
            bibl.append(pg)
        else:
            pg = ET.Element("BIBLSCOPE", attrib={"TYPE":"pg"})
            pg.text = entry["Page Number"]
            bibl.append(pg)

        #pages
        if page_end:
            page_range = [str(x) for x in range(int(entry["Page Number"]), int(page_end) + 1)]
            #print("range", page_range)
            for p in root.iter("P"):
                try:
                    page_num = p.find("PB").attrib["N"]
                    #print(page_num)
                    if page_num in page_range:
                        div1.append(p)
                        pages_covered.add(p.find("PB").attrib["REF"])
                        #print("added", page_num)
                except:
                    continue
        else:
            for p in root.iter("P"):
                try:
                    page_num = p.find("PB").attrib["N"]
                    if page_num == entry["Page Number"]:
                        div1.append(p)
                        pages_covered.add(p.find("PB").attrib["REF"])
                        #print("added", page_num)
                        break
                except:
                    continue
        divs.append(div1)

    #----------------------------------
    #----Adding Uncategorized Pages----
    #--(Mostly Front and Back Matter)--
    #-----------------------------------

    for pb in [x.find("PB") for x in root.iter("P") if x.find("PB") is not None]:
        # print(pb.attrib["REF"])
        if pb.attrib["REF"] not in pages_covered:
            # print("not used so far")
            div1 = ET.Element("DIV1", attrib={"NODE" : f"{ID} : 000"})
            bibl = ET.Element("BIBL")
            title = ET.Element("TITLE")
            title.text = "Advertisement" if pb.attrib["FTR"] == "ADV" else "Front Matter"
            bibl.append(title)
            div1.append(bibl)
            pg = ET.Element("P")
            pg.append(pb)
            div1.append(pg)
            #now where to put it..
            num = int(pb.attrib["REF"].replace("p", "").split(".")[0])
            #if page is less than smallest of already covered pages
            if num <= min([int(x.replace("p","").split(".")[0]) for x in pages_covered]):
                divs.insert(0, div1)
                pages_covered.add(pb.attrib["REF"])
                # print('\tadded to start', num)
            #if page is more than largest of already covered pages
            elif num >= max([int(x.replace("p","").split(".")[0]) for x in pages_covered]):
                divs.append(div1)
                pages_covered.add(pb.attrib["REF"])
                # print('\tadded to end', num)
            #somewhere in the middle
            else:
                location = None
                # print(f"assessing location of {num}")
                for idx,things in enumerate(divs):
                    before_number = int([x for x in divs[idx-1].iter("PB")][0].attrib["REF"].replace("p","").split(".")[0])
                    next_number = int([x for x in divs[idx+1].iter("PB")][0].attrib["REF"].replace("p","").split(".")[0])
                    if num > before_number and num < next_number:
                        divs.insert(idx,div1)
                        pages_covered.add(pb.attrib["REF"])
                        # print("before", before_number, "now", num, "next", next_number)
                        break

    #---------------------------------------
    #--Consolidating Front and Back Matter--
    #---------------------------------------

    deleters = []
    # print(len(divs))
    for i in range(0,len(divs)):
        if i != 0:
            if divs[i].find("BIBL").find("TITLE").text == divs[i-1].find("BIBL").find("TITLE").text:
                # print("found consolidation instance")
                for p in list(divs[i].iter("P")):
                    divs[i-1].append(p)
                    # print("added something")
                    # print([x.text for x in divs[-1].iter()])
                deleters.append(divs[i])
    print("done with consolidation loop")

    for thing in deleters:
        divs.remove(thing)


    #--------------------------------
    #--Create Table of Contents DIV--
    #--------------------------------
        
    #-Creat TOC Div
    toc_div1 = ET.Element("DIV1")
    toc_div1
    toc_bibl = ET.Element("BIBL")
    toc_title = ET.Element("TITLE")
    toc_title.text = "Table of Contents"
    toc_bibl.append(toc_title)
    toc_div1.append(toc_bibl)

    #find location
    toc_loc = None
    for idx, div in enumerate(divs):
        #print([x for x in div.iter("PB")][0].attrib["REF"])
        if [x for x in div.iter("PB")][0].attrib["REF"] == "p0003.tif":
            toc_p = ET.Element("P")
            toc_pb = ET.Element("PB")
            for key,val in [x for x in div.iter("PB")][0].attrib.items():
                #print(key,val)
                toc_pb.attrib[key] = val
            toc_pb.tail = [x for x in div.iter("PB")][0].tail
            toc_p.append(toc_pb)
            toc_div1.append(toc_p)
            toc_loc = idx
            break

    if toc_loc:
        divs.insert(toc_loc, toc_div1)
        print("---inserted toc div")
    else:
        print("---did not insert toc div")

    #-------------------------------
    #--Reassign REF Node Attribute--
    #-------------------------------

    node_count = 1
    for div in divs:
        div.attrib["NODE"] = f"{ID}:{node_count}"
        node_count += 1

    #------------------------------
    #------Chop Out Page OCR-------
    #(except for table of contents)
    #-------------------------------

    for idx,div in enumerate(divs):
        if div != divs[-1]:
            if [x for x in div.iter("TITLE")][0].text not in ("Table of Contents", "Adverstisements") and [x for x in divs[idx+1].iter("TITLE")][0].text not in ("Table of Contents", "Adverstisements"):
            #if the last page of the current article div matches the first page of the next article div...  
                if [x for x in div.iter('PB')][-1].attrib["REF"] == [x for x in divs[idx+1].iter('PB')][0].attrib["REF"]:

                    title = [x for x in divs[idx+1].iter("TITLE")][0].text
                    line_break1 = None
                    line_break2 = None

                    #-Line Break 1 (for current DIV)
                    for i, line in enumerate([x for x in divs[idx].iter('PB')][-1].tail.splitlines()):
                        if title in line:
                            line_break1 = i
                            print('found break')
                            break
                    if not line_break1:
                        line_break1 = process.extractOne(title, [line for line in list(divs[idx].iter("PB"))[-1].tail.splitlines()[2:]])[0]
                        line_break1 = list(list(divs[idx].iter("PB"))[-1].tail.splitlines()).index(line_break1)
                        print("processed line break", line_break1)
                    if not line_break1:
                        print("more issues")

                    #-Line Break 2 (for Next DIV)
                    for i, line in enumerate([x for x in divs[idx+1].iter('PB')][0].tail.splitlines()):
                        if title in line:
                            line_break2 = i
                            print('found break')
                            break
                    if not line_break2:
                        line_break2 = process.extractOne(title, [line for line in list(divs[idx+1].iter("PB"))[0].tail.splitlines()[2:]])[0]
                        line_break2 = list(list(divs[idx+1].iter("PB"))[0].tail.splitlines()).index(line_break2)
                        print("processed line break", line_break2)
                    if not line_break2:
                        print("more issues")

                    #-Trimming Page Text for Current DIV
                    new_pg = ET.Element("P")
                    new_pb = ET.Element("PB")
                    for key,val in [x for x in div.iter('PB')][-1].attrib.items():
                        new_pb.attrib[key] = val
                    new_pb.tail = "  \n\n" + "\n".join([x for x in div.iter('PB')][-1].tail.splitlines()[:line_break1]+["\n","\n"])
                    new_pg.append(new_pb)
                    divs[idx][-1] = new_pg

                    #-Trimming Page Text for Next DIV
                    new_pg2 = ET.Element("P")
                    new_pb2 = ET.Element("PB")
                    for key,val in [x for x in divs[idx+1].iter("PB")][0].attrib.items():
                        new_pb2.attrib[key] = val
                    new_pb2.tail = "  \n\n" + "\n".join([x for x in divs[idx+1].iter("PB")][0].tail.splitlines()[line_break2:]+["\n","\n"])
                    new_pg2.append(new_pb2)
                    divs[idx+1][1] = new_pg2

            else:
                print("not necessary")

    #--------------------------
    #--Chop Table of Contents--
    #--------------------------

    for idx,div in enumerate(divs):
        if [x for x in div.iter("TITLE")][0].text == "Table of Contents":
            title = [x for x in divs[idx+1].iter("TITLE")][0].text
            found = 0
            toc_line_break = None
            for line_index, line in enumerate([x for x in div.iter("PB")][0].tail.splitlines()):
                if title.lower() in line.lower() or fuzz.partial_ratio(title, line) > 70:
                    if found == 0:
                        found += 1
                        print("found first tile instance")
                    elif found == 1:
                        toc_line_break = line_index
                        print("found toc line break:", toc_line_break, line)
                    else:
                        print("issue!")
            toc_text = [x for x in div.iter('PB')][0].tail
            #print("found toc line break:", toc_line_break, "\n".join(toc_text.splitlines()[toc_line_break-1:]))
            if toc_line_break:
                    #toc page
                    new_pg = ET.Element("P")
                    new_pb = ET.Element("PB")
                    for key,val in [x for x in div.iter('PB')][-1].attrib.items():
                        new_pb.attrib[key] = val
                    new_pb.tail = "  \n\n" + "\n".join(toc_text.splitlines()[:toc_line_break]+["\n","\n"])
                    new_pg.append(new_pb)
                    div[1] = new_pg

                    new_pg = ET.Element("P")
                    new_pb = ET.Element("PB")
                    for key,val in [x for x in divs[idx+1].iter("PB")][0].attrib.items():
                        new_pb.attrib[key] = val
                    new_pb.tail = "  \n\n" + "\n".join(toc_text.splitlines()[toc_line_break:]+["\n","\n"])
                    new_pg.append(new_pb)
                    divs[idx+1][1] = new_pg

    #-----------------------------------------------
    #--Check lines to detect blanks pages included--
    #----------------(In progress)------------------
    #-----------------------------------------------
    #--In progress--
    for div in divs:
        #print("div:", div.attrib["NODE"])
        for page in div.iter("PB"):
            print(f"page length for {page.attrib['REF']}", len(page.tail.splitlines()))
            if len(page.tail.splitlines()) < 10:
                print("\t", page.tail)

    #-------------------------------------
    #--Replace XML Body with new content--
    #-------------------------------------

    text = root.find("./TEXT")
    body = root.find("./TEXT/BODY")
    text.remove(body)
    new_body = ET.Element("BODY")
    for div1 in divs:
        new_body.append(div1)
    text.append(new_body)

    #--for whole of gandf.xml; change node 
    editorial_decl = [x for x in root.iter("EDITORIALDECL")][0]
    editorial_decl.attrib["N"] = "2"
    ed_p = [x for x in editorial_decl.iter("P")][0]
    ed_p.text = "This electronic text file was created by Optical Character Recognition (OCR). No corrections have been made to the OCR-ed text and no editing has been done to the content of the original document. Encoding has been done using the recommendations for Level 2 of the TEI in Libraries Guidelines. Digital page images are linked to the text file."

    #-----------------
    #--Write Results--
    #-----------------

    tree.write(f'new_{ID}.xml')
    # tree.write(f'new_gandf_2.xml')
    print("Wrote it")

if __name__ == "__main__":
    main()
    print("done")