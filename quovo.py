from bs4 import BeautifulSoup
import requests
import re


class Edgar:
    """
    Given a ticker, the Edgar class searches all the 13f-hr documents, finds those written in XML, and creates tab
    delimited txt files.
    """

    def __init__(self, value):
        """
        Creates instance object ticker as string of digits

        """
        self.ticker = value

    def get_xml_docs(self, start="0"):
        """
        # Generator object, uses self.ticker and yields requests.models.response object
        # :param start : Param from get_xml_docs recursive call, occurs if there exists > 100 items to iterate on Edgar
        #                Search
        # :type start : string, multiple of 100
        # :returns : Yields http request, requests.models.response object
        """
        ticker1 = self.ticker
        edgar_tick_url = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany" \
                         "&CIK={0}" \
                         "&type=13f-hr" \
                         "&start={1}" \
                         "&dateb=&owner=exclude&count=100".format(ticker1, start)
        edgar_search_html = requests.get(edgar_tick_url)
        soup = BeautifulSoup(edgar_search_html.text, "lxml")
        elements = soup.find("table", class_="tableFile2", summary="Results").findAll("tr")
        elements.pop(0)  # First html element does not hold information
        # Iterating elements on search page
        for trElement in elements:
            index_page_url = "http://www.sec.gov" + trElement.find("a", id="documentsbutton")['href']
            index_page_html = requests.get(index_page_url)
            soup2 = BeautifulSoup(index_page_html.text)
            allLinkElements = soup2.findAll("a")
            #Iterating through all link elements ("a") on index page
            for link in allLinkElements:
                if ".txt" in link.text:  # Looking for text files
                    document_link = "http://www.sec.gov" + link['href']
                    document_xml = requests.get(document_link)
                    if "xml" in document_xml.text:  # looking for the xml files
                        yield document_xml
        # Going to next search page
        if "Items 1 - 100" in soup.findAll("td")[6].text:
            start = str(int(start) + 100)
            self.get_xml_docs(start)

    def make_text_file(self, args):
        """
        # :param : args
        # :type : strings
        # :returns : Creates .txt files
        """
        file_name, form_info, form_specific_heading_string, form_specific_string, table_header, list_of_table_info = args
        f = open(file_name, 'w')
        f.write(form_info)
        f.write(form_specific_heading_string)
        f.write(form_specific_string)
        f.write(table_header)
        list_of_table_info = list_of_table_info
        for line in list_of_table_info:
            f.write(line)

    def form_parser(self, xml_document):

        """
        # Used to parse XML Documents. Takes requests.models.Response object returns strings.
        # :rtype : object
        # :param xml_document:
        """
        # Getting title for .txt file. Title written as such: ticker_effectivenessDate.
        for line in xml_document:
            if "EFFECTIVENESS DATE:" in line:
                effectiveness_date = re.findall("[0-9]{8}", line)[2]
            if "CENTRAL INDEX KEY" in line:
                CIK = re.findall('[0-9]{10}', line)[0]
                file_name = CIK + "_" + effectiveness_date + ".txt"
                break
        # Getting form info top
        form_info = ""
        for line in xml_document:

            if "/SEC-HEADER>" in line:
                break
            form_info += line
        form_info = form_info.replace("<", "")
        form_info = form_info.replace(">", " ")

        # Scraping from XML Doc
        soup = BeautifulSoup(xml_document.text)
        # Scraping form specific information
        form_specific_string = "\n\n" + \
                               soup.find("submissiontype").text + "\t" + \
                               soup.find("livetestflag").text + "\t" + \
                               soup.find("cik").text + "\t" + \
                               soup.find("ccc").text + "\t" + \
                               soup.find("reportcalendarorquarter").text + "\t" + \
                               soup.find("isamendment").text + "\t" + \
                               soup.find("periodofreport").text + "\t" + \
                               soup.find("name").text + "\t" + \
                               soup.find("coverpage").find("ns1:street1").text + "\t" + \
                               soup.find("coverpage").find("ns1:city").text + "\t" + \
                               soup.find("coverpage").find("ns1:stateorcountry").text + "\t" + \
                               soup.find("coverpage").find("ns1:zipcode").text + "\t" + \
                               soup.find("coverpage").find("reporttype").text + "\t" + \
                               soup.find("coverpage").find("form13ffilenumber").text + "\t" + \
                               soup.find("coverpage").find("provideinfoforinstruction5").text + "\t" + \
                               soup.find("signatureblock").find("name").text + "\t" + \
                               soup.find("signatureblock").find("title").text + "\t" + \
                               soup.find("signatureblock").find("phone").text + "\t" + \
                               soup.find("signatureblock").find("signature").text + "\t" + \
                               soup.find("signatureblock").find("city").text + "\t" + \
                               soup.find("signatureblock").find("stateorcountry").text + "\t" + \
                               soup.find("signatureblock").find("signaturedate").text + "\t" + \
                               soup.find("summarypage").find("otherincludedmanagerscount").text + "\t" + \
                               soup.find("summarypage").find("tableentrytotal").text + "\t" + \
                               soup.find("summarypage").find("tablevaluetotal").text + "\t" + \
                               soup.find("summarypage").find("isconfidentialomitted").text + "\t"

        # Heading for form specific data
        form_specific_heading_string = "\n\nSubmission type\tLive Test Flag\tCIK\tCCC\tReport Calendar Quarter\t" \
                                       "Is Amendment\tPeriod of Report\tName\tStreet\tCity\tState Or Country\t" \
                                       "Zipcode\tReport Type\tFrom File Number\tProvide Info for Instructions\t" \
                                       "Name\tTitle\tPhone\tSignature\tCity\tState Or Country\tSignature Date\t" \
                                       "Other Included Managers Count\tTable Entry Total\tTable Entry Value\t" \
                                       "Is Confidential Omitted\t"
        # Making sure the count of items for the form specific data is coincides with the item count of the heading
        assert form_specific_string.count("\t") == form_specific_heading_string.count("\t")
        #Table info header:
        table_header = '\n\n\nName of Issuer\ttitle of Class\tcusip\tvalue\tshares or prn amount\tsh/prn\tinvestment' \
                       'discretion\tvotingAuthority_sole\tvotingAuthority_shared\tvotingAuthority_None \n\n'
        # Scraping table information
        list_of_table_info = []
        for item in soup.find("informationtable").findAll("infotable"):
            name_of_issuer = item.find("nameofissuer").text
            title_of_class = item.find("titleofclass").text
            cusip = item.find("cusip").text
            value = item.find("value").text
            shrs_or_prn_amt_number = item.find("shrsorprnamt").find("sshprnamt").text
            shrs_or_prn_amt_type = item.find("shrsorprnamt").find("sshprnamttype").text
            investment_discretion = item.find("investmentdiscretion").text
            voting_authority_sole = item.find("sole").text
            voting_authority_shared = item.find("shared").text
            voting_authority_none = item.find("none").text
            line_addition = name_of_issuer + "\t" + title_of_class + "\t" + cusip + "\t" + value + "\t" + \
                            shrs_or_prn_amt_number + "\t" + shrs_or_prn_amt_type + "\t" + investment_discretion + "\t" \
                            + voting_authority_sole + "\t" + voting_authority_shared + '\t' + \
                            voting_authority_none + "\n"
            list_of_table_info.append(line_addition)

        return file_name, form_info, form_specific_heading_string, form_specific_string, table_header, \
               list_of_table_info

    def main(self):
        """
        Comes in methods in sequence to produce text files
        """
        for xml in self.get_xml_docs():
            self.make_text_file(self.form_parser(xml))


# Creating the instance
B = Edgar("0001166559")
# Calling Main
B.main()
