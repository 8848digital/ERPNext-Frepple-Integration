# Copyright (c) 2024, Drayang Chua and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe,json
from frappe.model.document import Document
from frappe import _

from datetime import datetime
from datetime import time
from datetime import timedelta
from frappe.utils import add_to_date

from frappe.integrations.utils import make_get_request, make_post_request, create_request_log
from frappe.utils import get_request_session

import requests
from requests.structures import CaseInsensitiveDict
class FreppleDataImport(Document):
	pass

@frappe.whitelist()
def import_data(doc):
	doc = json.loads(doc)

	import_datas = []

	if doc["frepple_item"]:
		import_frepple_item()
		import_datas.append("Frepple Demand")

	# Output msg 
	for import_data in import_datas:
		frappe.msgprint(_("{0} is exported.").format(import_data))

@frappe.whitelist()
def get_frepple_params(api=None,filter = None):
	if not api:
		api = "" #default get the demand(=sales order in ERPNext) list from frepple
	if not filter:
		filter = ""

	frepple_settings = frappe.get_doc("Frepple Settings")
	temp_url = frepple_settings.url.split("//")
	url1 = "http://"+ frepple_settings.username + ":" + frepple_settings.password + "@" + temp_url[1] + "/api/input/"
	url2 = "/"
	# "/?format=json"
	# "/?format=api"

	#Concatenate the URL
	url = url1 +  api + url2 + filter
	# example outcome : http://admin:admin@192.168.112.1:5000/api/input/manufacturingorder/

	headers= {
		'Content-type': 'application/json; charset=UTF-8',
		'Authorization': frepple_settings.authorization_header,
	}
	print(url+ "-------------------------------------------------------------------------")

	return url,headers
def import_frepple_item():
	api = "item" 
	url,headers = get_frepple_params(api=api,filter=None)
	output = make_get_request(url,headers=headers)
	print(output)
	for item in output:
		if not frappe.db.exists("Frepple Item",item.name):
			new_item = frappe.new_doc("Frepple Item")
			new_item.item = item.name
			new_item.description = item.item_name
			new_item.uom = item.stock_uom
			new_item.cost = item.valuation_rate
			new_item.item_owner = item.owner
			new_item.insert()