# -*- coding: utf-8 -*-
# Copyright (c) 2022, Drayang Chua and contributors
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

from frepple.frepple.doctype.frepple_data_export.frepple_data_export import get_frepple_params,export_sales_orders

class FreppleRunPlan(Document):
	pass

@frappe.whitelist()
def run_plan(doc):
	doc = json.loads(doc)

	if doc["update_frepple"]:
		export_sales_orders()
		export_manufacturing_orders()
		export_purchase_orders()

	constraint= 0
	plantype = 1
	# filter = "/execute/api/runplan/?"
	
	if doc['constraint']:
		plantype = 1
	if doc['unconstraint']:
		plantype = 2
	if doc['capacity']:
		constraint = constraint + 4
	if doc['lead_time']:
		constraint = constraint + 1
	if doc['release_fence']:
		constraint = constraint + 8

	filter = "/execute/api/runplan/?constraint="+ str(constraint)+"&plantype="+ str(plantype)+"&env=supply"
	frepple_settings = frappe.get_doc("Frepple Settings")
	temp_url = frepple_settings.url.split("//")
	url = "http://"+ frepple_settings.username + ":" + frepple_settings.password + "@" + temp_url[1] + filter
	headers= {
		'Content-type': 'application/json; charset=UTF-8',
		'Authorization': frepple_settings.authorization_header,
	}

	output = make_post_request(url,headers=headers, data=None)

	frappe.msgprint(
		msg='Plan have been runned successfully.',
		title='Success',
	)

	return output

@frappe.whitelist()
def generate_result(doc):
	run_pan_doc=json.loads(doc)
	
	import_datas = []
	# Import manufacturing order
	if run_pan_doc.get('import_mo')==1:
		data = import_manufacturing_order()
		# return data
		import_datas.append("Manufacturing Order Result")
		generate_manufacturing_order(data)

	# Import purchase order
	if run_pan_doc.get('import_po')==1:
		data = import_purchase_order()
		import_datas.append("Purchase Order Result")
		generate_purchase_order(data)
	
	if run_pan_doc.get('import_item_distribution')==1:
		data = import_item_distribution()
		import_datas.append("Item Distribution Result")
		generate_item_distribution(data)
	
	if run_pan_doc.get('import_item_supplier')==1:
		data = import_item_supplier()
		import_datas.append("Item Supplier Result")
		generate_item_supplier(data)
	
	if run_pan_doc.get('import_operation_resource')==1:
		data = import_operation_resource()
		import_datas.append("Frepple Operation Resource")
		generate_op_resource(data)
	
	if run_pan_doc.get('import_operation_material')==1:
		data = import_operation_material()
		import_datas.append("Frepple Operation Material")
		generate_operation_material(data)

	if run_pan_doc.get('import_distribution_order')==1:
		data = import_distribution_order()
		import_datas.append("Frepple Distribtion Order")
		generate_distribution_order(data)
	
	if run_pan_doc.get('import_demand')==1:
		data = import_demand_order()
		import_datas.append("Frepple Demand")
		generate_demand_order(data)
	
	
	if run_pan_doc.get('import_inv_detail')==1:
		data = import_inv_detail()
		import_datas.append("Frepple Inventory Detail")
		generate_inv_detail(data)

	if run_pan_doc.get('import_inventory_policy')==1:
		data = import_inv_policy_detail()
		import_datas.append("Frepple Inventory Detail")
		generate_inv_policy_detail(data)
	# Output msg 
	if run_pan_doc['import_op_dependency']:
		data = import_op_dependency()
		import_datas.append("Frepple Operation Dependency")
		generate_op_dependency_detail(data)

	if run_pan_doc['import_sub_operation']:
		data = import_sub_operation()
		import_datas.append("Frepple Sub Operation")
		generate_sub_operation_details(data)	

	for import_data in import_datas:
		frappe.msgprint(_("{0} is imported.").format(import_data))


def export_manufacturing_orders():
	api = "manufacturingorder" #equivalent work order
	url,headers = get_frepple_params(api=api,filter=None)
	
	mos = frappe.db.sql(
		"""
		SELECT latest_reference,operation,status,quantity
		FROM `tabFrepple Manufacturing Order`
		""",
	as_dict=1)
		
	for mo in mos:
		data = json.dumps({
			"reference": mo.latest_reference,
			# "operation": mo.operation,
			"status": mo.status,
			# "quantity": mo.quantity,
		})
		output = make_post_request(url,headers=headers, data=data)

def export_purchase_orders():
	api = "purchaseorder" #equivalent purchase order
	url,headers = get_frepple_params(api=api,filter=None)
	
	pos = frappe.db.sql(
		"""
		SELECT latest_reference,supplier,status
		FROM `tabFrepple Purchase Order`
		""",
	as_dict=1)
		
	for po in pos:
		data = json.dumps({
			"reference": po.latest_reference,
			# "supplier": po.supplier,
			"status": po.status,
		})
		output = make_post_request(url,headers=headers, data=data)



def import_manufacturing_order():
	api = "manufacturingorder"
	
	''' With filtering'''
	# filter = "?name=SAL-ORDER-0002"
	# filter = None
	# filter = "?status__contain=open"
	# url,headers = get_frepple_params(api=None,filter=filter)
	
	filter = "?operation_in=BOM"
	# filter = "?operation_in=BOM"
	
	url,headers = get_frepple_params(api=api,filter=filter)
	outputs = make_get_request(url,headers=headers)
	# print(type(outputs))
	# idx = 0
	# for output in outputs:
	# 	print(output["operation"])
	# 	print(output["operation"].split("@"))
	# 	if (len(output["operation"].split("@")) > 1): #routing type operation should only have 1 element, use this to filter out the routing type
	# 		print("Delete")
	# 		del outputs[idx]
	# 	idx = idx + 1

	# print(outputs)
	# Delete dictionary from list using list comprehension
	res = [output for output in outputs if not (len(output["operation"].split("@")) > 1)]

	return res

def generate_manufacturing_order(data):
	for i in data:
		# print(i["plan"])
		# idx = 0
		# demand = (list(i["plan"]["pegging"].keys())[idx])

		demands = (list(i["plan"]["pegging"].keys()))
		for demand in demands:
			mos = frappe.db.sql(
				"""
				SELECT name,demand
				FROM `tabFrepple Manufacturing Order`
				WHERE demand = %s
				""",
			demand,as_dict=1)
			
			# if not frappe.db.exists("Frepple Manufacturing Order",i["reference"]):
			if not frappe.db.exists("Frepple Manufacturing Order",{"name":i["reference"],"operation":i['operation']}):
				#create new document
				new_doc = frappe.new_doc("Frepple Manufacturing Order")
				new_doc.reference = i["reference"]
				new_doc.latest_reference = i["reference"]
				new_doc.operation = i["operation"]
				new_doc.status = i["status"]
				new_doc.quantity = i["quantity"]
				new_doc.completed_quantity = i["quantity_completed"]
				new_doc.start_date = datetime.fromisoformat(i["startdate"])
				new_doc.end_date = datetime.fromisoformat(i["enddate"])
				new_doc.demand = demand
				new_doc.insert()
				
			# elif frappe.db.exists("Frepple Manufacturing Order",i["reference"]) and len(mos)== 0:
			# 	frappe.log_error("FMO Exsist",str(i))
			# 	continue
			else:#update

				if frappe.db.exists("Frepple Manufacturing Order",i["reference"]):
					existing_doc = frappe.get_doc("Frepple Manufacturing Order",i["reference"])
					frappe.db.set_value('Frepple Manufacturing Order', i["reference"], #Update the status
					{
						'latest_reference': i["reference"],
						'operation': i["operation"],
						'status': i["status"],
						'quantity': i["quantity"],
						# 'completed_quantity': i["quantity_completed"],
						'start_date': datetime.fromisoformat(i["startdate"]),
						'end_date': datetime.fromisoformat(i["enddate"])
					})
					# existing_doc.reference = i["reference"]
					# existing_doc.operation = i["operation"]
					# existing_doc.status = i["status"]
					# existing_doc.quantity = i["quantity"]
					# existing_doc.completed_quantity = i["quantity_completed"]
					# existing_doc.start_date = datetime.fromisoformat(i["startdate"])
					# existing_doc.end_date = datetime.fromisoformat(i["enddate"])
					# existing_doc.save(ignore_permissions=True, ignore_version=True)
					# existing_doc.reload()


def import_purchase_order():
	api = "purchaseorder"
	
	''' With filtering'''
	# filter = "?name=SAL-ORDER-0002"
	# filter = None
	# filter = "?status__contain=open"
	# url,headers = get_frepple_params(api=None,filter=filter)
	
	filter = "?status=proposed"
	
	url,headers = get_frepple_params(api=api,filter=filter)
	output = make_get_request(url,headers=headers)

	return output

def generate_purchase_order(data):

	for i in data:
		pos = frappe.db.sql(
			"""
			SELECT name,item,supplier
			FROM `tabFrepple Purchase Order`
			WHERE item = %s and supplier = %s
			""",
		[i["item"],i["supplier"]],as_dict=1)
		if len(pos) == 0:
		# if not frappe.db.exists("Frepple Purchase Order",i["reference"]):
			new_doc = frappe.new_doc("Frepple Purchase Order")
			new_doc.reference = i["reference"]
			new_doc.latest_reference = i["reference"]
			new_doc.supplier = i["supplier"]
			new_doc.status = i["status"]
			new_doc.ordering_date = datetime.fromisoformat(i["startdate"])
			new_doc.receive_date =  datetime.fromisoformat(i["enddate"])
			new_doc.item = i["item"]
			new_doc.quantity =i["quantity"]
			new_doc.insert()
		else: #update
			existing_doc = frappe.get_doc("Frepple Purchase Order",pos[0].name)
			frappe.db.set_value('Frepple Purchase Order', pos[0].name, #Update the status
			{
				'latest_reference': i["reference"],
				"ordering_date" : datetime.fromisoformat(i["startdate"]),
				"receive_date" :  datetime.fromisoformat(i["enddate"]),
				"quantity" : i["quantity"]
			})


def import_item_distribution():
	api = 'itemdistribution'
	url,headers = get_frepple_params(api=api,filter=None)
	output = make_get_request(url,headers=headers)
	return output

def generate_item_distribution(data):
	for id in data:
		if not frappe.db.exists('Frepple Item Distribution',{'item':id.get('item'),
													   'origin': id.get('origin'),"destination":id.get('location')}):
				
			item_dis_doc = frappe.get_doc({
				"doctype":"Frepple Item Distribution",
				'item': id.get('item'),
				'origin': id.get('origin'),
				"destination":id.get('location'),
				"leadtime":convert_to_millisecond(id.get('leadtime')),
				'priority':id.get('prority'),
				'effetive_start_datetime': fetch_date(id.get('effective_start')),
				'effective_end_datetime':fetch_date(id.get('effective_end')) 
			})
			item_dis_doc.save()
		else:
			continue

def import_item_supplier():
	api = 'itemsupplier'
	url,headers = get_frepple_params(api=api,filter=None)
	output = make_get_request(url,headers=headers)
	return output

def generate_item_supplier(data):
	for id in data:
		if not frappe.db.exists('Frepple Item Supplier',{'item':id.get('item'),
													   "supplier":id.get('supplier')}):
	
			item_supplier_doc = frappe.get_doc({
				"doctype":"Frepple Item Supplier",
				'item': id.get('item'),
				"supplier":id.get('supplier'),
				"supplier_cost":id.get('cost'),
				"leadtime":convert_to_millisecond(id.get('leadtime')),
				'sizeminimum': id.get('sizeminimum'),
				'sizemultiple': id.get('sizemultiple'),
				'sizemaximum': id.get('sizemaximum'),
				'cost': id.get('cost'),
				'priority':id.get('prority'),
				'hard_safety_leadtime': convert_to_millisecond(id.get('hard_safety_leadtime')),
				'extra_safety_leadtime':convert_to_millisecond(id.get('extra_safety_leadtime')),
				"effective_start":fetch_date(id.get('effective_start')),
				"effective_end": fetch_date(id.get('effective_end')),
			})
			item_supplier_doc.save()
		else:
			continue


def convert_to_millisecond(time_str):
	if time_str:
		parts = time_str.split()
		days = 0
		hours, minutes, seconds = 0, 0, 0
		if len(parts) == 2:
			
			days = int(parts[0])
			time_part = parts[1]
		else:
			time_part = parts[0]
		
		hours, minutes, seconds = map(int, time_part.split(':'))
		
		milliseconds = (
			(days * 24 * 3600 + hours * 3600 + minutes * 60 + seconds)
		)
		
		return milliseconds
	else:
		return 0


def import_operation_resource():
	api = 'operationresource'
	url,headers = get_frepple_params(api=api,filter=None)
	output = make_get_request(url,headers=headers)
	return output


def generate_op_resource(data):
	for op in data:
		if op.get('search') == 'PRIORITY':
			search="priority" 
		elif op.get('search') == 'MINCOST':
			search=="minimum cost" 
		elif op.get('search') =="MINPENALTY":
			search="minimum penalty" 
		elif op.get('search') =="MINCOSTPENALTY":
			search="minimum cost plus penalty"
		if not frappe.db.exists('Frepple Operation Resource',{'operation':op.get("operation"),'resource':op.get('resource')}):
			op_resource_doc = frappe.get_doc({
				'doctype':'Frepple Operation Resource',
				"operation":op.get('operation'),
				"resource":op.get('resource'),
				'setup':op.get('setup'),
				"fixed_qty":op.get('quantity_fixed'),
				"quantity":op.get('quantity'),
				"effective_start":fetch_date(op.get('effective_start')),
				"effective_end":fetch_date(op.get('effective_end')),
				"search_mode":search,
				"alt_name":op.get('name'),
				"priority":op.get('priority'),
				"type":op.get('type')
			})
			op_resource_doc.save()
		else:
			continue


def import_operation_material():
	api = 'operationmaterial'
	url,headers = get_frepple_params(api=api,filter=None)
	output = make_get_request(url,headers=headers)
	return output


def generate_operation_material(data):
		for op in data:
			if not frappe.db.exists('Frepple Operation Material',{'operation':op.get("operation"),'item':op.get('item')}):
				search=None
				if op.get('search') == 'PRIORITY':
					search="priority" 
				elif op.get('search') == 'MINCOST':
					search="minimum cost" 
				elif op.get('search') =="MINPENALTY":
					search="minimum penalty" 
				elif op.get('search') =="MINCOSTPENALTY":
					search="minimum cost plus penalty"
				
				op_material_doc = frappe.get_doc({
					'doctype':'Frepple Operation Material',
					"operation":op.get('operation'),
					"item":op.get('item'),
					'trnfd_batch_qty':op.get('transferbatch'),
					"fixed_qty":op.get('quantity_fixed'),
					"quantity":op.get('quantity'),
					"effective_start":fetch_date(op.get('effective_end')),
					"effective_end":fetch_date(op.get('effective_end')),
					"search_mode":search,
					"alt_name":op.get('name'),
					"priority":op.get('priority'),
					"offset":convert_to_millisecond(op.get('offset')),
					"type":op.get('type'),
				})
				op_material_doc.save()
			else:
				continue

def import_distribution_order():
	api = 'distributionorder'
	url,headers = get_frepple_params(api=api,filter=None)
	output = make_get_request(url,headers=headers)
	return output


def generate_distribution_order(data):
	for dis_order in data:
		if not frappe.db.exists('Frepple Distribution Order',{'reference_number':dis_order.get('reference')}):
			
			distribution_order_doc = frappe.get_doc({
				'doctype':"Frepple Distribution Order",
				"item":dis_order.get('item'),
				"reference_number":dis_order.get('reference'),
				"source_warehouse":dis_order.get("origin"),
				"target_warehouse":dis_order.get("destination"),
				"quantity":dis_order.get("quantity"),
				"status":dis_order.get('status').capitalize(),
				"shipping_date":fetch_date(dis_order.get('startdate')),
				"receipt_date":fetch_date(dis_order.get('enddate')),
				"expiry_date":fetch_date(dis_order.get('expiry')),
				"batch":dis_order.get('batch')		
			})
			distribution_order_doc.save()
		elif frappe.db.exists('Distribution Order',{'reference_number':dis_order.get('reference')}):
			distribution_order_doc = frappe.db.set_value('Frepple Distribtuion Order',dis_order.get('reference'),{
				"quantity":dis_order.get("quantity"),
				"status":dis_order.get('status').capitalize(),
				"batch":dis_order.get('batch')		
			})
			distribution_order_doc.save()
		else:
			continue

def import_demand_order():
	api = 'demand'
	url,headers = get_frepple_params(api=api,filter=None)
	output = make_get_request(url,headers=headers)
	return output


def generate_demand_order(data):
	for demand in data:
		if frappe.db.exists('Frepple Demand',{'name':demand.get('name')}):
			demand_doc = frappe.db.set_value("Frepple Demand",demand.get('name'),{
				"due":fetch_date(demand.get('deliverydate')),
				"status":demand.get('status'),
				
			})
			
			


def import_inv_detail():
	api = 'operationplanmaterial'
	url,headers = get_frepple_params(api=api,filter=None)
	output = make_get_request(url,headers=headers)
	return output


def generate_inv_detail(data):
	for inv_data in data:
		if not frappe.db.exists('Frepple Inventory Detail',{"id":inv_data.get('id')}):
			inv_doc = frappe.get_doc({
			"doctype":"Frepple Inventory Detail",
			"id":inv_data.get('id'),
			"item":inv_data.get('item'),
			"location":inv_data.get('location'),
			"material_status":inv_data.get('status').capitalize(),
			"quantity":inv_data.get('quantity'),
			"date":fetch_date(inv_data.get('flowdate')),
			})
			inv_doc.save()




def import_inv_policy_detail():
	api = "inventoryplanning"
	url,headers = get_frepple_params(api=api,filter="inventoryplanning")
	output = make_get_request(url,headers=headers)
	return output


def	generate_inv_policy_detail(data):
	for inv_policy in data:
		if not frappe.db.exists('Frepple Inventory Policies',{'name':inv_policy.get('id')}):
			inv_policy_doc=frappe.get_doc({
				"doctype":"Frepple Inventory Policies",
				"id":inv_policy.get('id'),
				"item":inv_policy.get('item'),
				"location":inv_policy.get('location'),
				"roq_minimum_quantity":inv_policy.get('roq_min_qty'),
				"roq_maximum_quantity":inv_policy.get('roq_max_qty'),
				"roq_minimum_period_of_cover":convert_to_millisecond(inv_policy.get('roq_min_poc')),
				"roq_maximum_period_of_cover":convert_to_millisecond(inv_policy.get('roq_max_poc')),
				"service_level":inv_policy.get('service_level'),
				#"demand_deviation":inv_policy.get(),
				#"lead_time":inv_policy.get(),
				"lead_time_deviation":convert_to_millisecond(inv_policy.get('leadtime_deviation')),
				"safety_stock_minimum_quantity":inv_policy.get('ss_min_qty'),
				"safety_stock_maximum_quantity":inv_policy.get('ss_max_qty'),
				"safety_stock_minimum_period_of_cover":convert_to_millisecond(inv_policy.get('ss_max_poc')),
				"safety_stock_maximum_period_of_cover":convert_to_millisecond(inv_policy.get('ss_max_poc'))
			})
			inv_policy_doc.save()
		else:
			continue

def  import_op_dependency():
	api = "operationdependency"
	url,headers = get_frepple_params(api=api,filter=None)
	output = make_get_request(url,headers=headers)
	return output

def generate_op_dependency_detail(data):
	for op_detail in data:
		if not frappe.db.exists('Frepple Operation Dependencies',{'name':op_detail.get("id")}):
			op_dependency_doc= frappe.get_doc({
				"doctype":"Frepple Operation Dependencies",
				'id':op_detail.get('id'),
				"operation":op_detail.get('operation'),
				"blocked_by_operation":op_detail.get('blockedby'),
				"quantity":op_detail.get('quantity'),
				"soft_safety_lead_time":convert_to_millisecond(op_detail.get('safety_leadtime')),
				"hard_safety_lead_time":convert_to_millisecond(op_detail.get('hard_safety_leadtime')),
				"source":op_detail.get('source')
			})
			op_dependency_doc.save()
		else:
			continue


def generate_sub_operation_details(data):
	print(data)
	for sub_operation in data:
		if not frappe.db.exists('Frepple Sub Operations',{'name':sub_operation.get("id")}):
			sub_operation_doc= frappe.get_doc({
				"doctype":"Frepple Sub Operations",
				'id':sub_operation.get('id'),
				"operation":sub_operation.get('operation'),
				"priority":sub_operation.get('priority'),
				"suboperation":sub_operation.get('suboperation'),
				"effective_start":fetch_date(sub_operation.get('effective_start')),
				"effective_end":fetch_date(sub_operation.get('effective_end')),
				"source":sub_operation.get('source')
			})
			sub_operation_doc.save()
		else:
			continue

def import_sub_operation():
	api = "suboperation"
	url,headers = get_frepple_params(api=api,filter=None)
	output = make_get_request(url,headers=headers)
	return output

def fetch_date(input_date):
	if input_date:
		date_str=datetime.strptime(input_date, '%Y-%m-%dT%H:%M:%S')
	else:
		date_str=None
	return date_str
