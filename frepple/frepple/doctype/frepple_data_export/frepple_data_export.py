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

class FreppleDataExport(Document):
	pass


@frappe.whitelist()
def export_data(doc):
	doc = json.loads(doc)
	print(doc)
	import_datas = []

	#Additional data
	if doc["frepple_calendar"]:
		export_calendars()
		import_datas.append("Frepple Calendar")
	if doc["frepple_calendar_bucket"]:
		export_calendar_buckets()
		import_datas.append("Frepple Calendar Bucket")

	# Sales
	if doc["frepple_item"]:
		export_items()
		import_datas.append("Frepple Item")
	if doc["frepple_customer"]:
		export_customers()
		import_datas.append("Frepple Customer")
	if doc["frepple_location"]:
		export_locations()
		import_datas.append("Frepple Location")

	# Inventory
	if doc["frepple_buffer"]:
		export_buffers()
		import_datas.append("Frepple Buffers")

	if doc["frepple_item_distribution"]:
		export_item_distribution()
		import_datas.append("Frepple Item Distribution")

	# Capacity
	if doc["frepple_resource"]:
		export_resources()
		import_datas.append("Frepple Resource")
	if doc["frepple_skill"]:
		export_skills()
		import_datas.append("Frepple Skill")
	# HAVENT include yet
	if doc["frepple_resource_skill"]:
		export_resource_skills()
		import_datas.append("Frepple Resource Skill")

	# Purchasing
	if doc["frepple_supplier"]:
		export_suppliers()
		import_datas.append("Frepple Supplier")
	if doc["frepple_item_supplier"]:
		export_item_suppliers()
		import_datas.append("Frepple Item Supplier")
	
	# Manufacturing
	if doc["frepple_operation"]:
		export_operations()
		import_datas.append("Frepple Operation")
	if doc["frepple_operation_material"]:
		export_operation_materials()
		import_datas.append("Frepple Operation Materials")

	if doc["frepple_operation_resource"]:
		export_operation_resources()
		import_datas.append("Frepple Operation Resource")

	if doc["frepple_demand"]:
		export_sales_orders()
		import_datas.append("Frepple Demand")
	
	# if doc['frepple_forecast']:
	# 	export_frepple_forecast()
	# 	import_datas.append("Frepple Forecast")
	
	# # Output msg 
	# if doc['distribution_order']:
	# 	import_datas.append("Frepple Distribution")
	# 	export_distribution_order()
	
	# if doc['frepple_sub_operation']:
	# 	import_datas.append("Frepple Sub Operation")
	# 	export_frepple_sub_operation()
	# if doc['frepple_operation_dependency']:
	# 	export_frepple_operation_dependencies()
	# 	import_datas.append("Frepple Operation Dependency")
	
	# if doc['frepple_resource_detail']:
	# 	export_resource_detail('Frepple Resource Detail')
	# 	import_datas('Frepple Resource Detail')
	
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
	end_point = "http://"+ frepple_settings.username + ":" + frepple_settings.password + "@" + temp_url[1] 
	if filter == 'inventoryplanning':
		url1=end_point + "/api/inventoryplanning/"
		url2 = "/"
		url = url1 +  api + url2
	else:
		url1=end_point + "/api/input/"
		url2 = "/"
		url = url1 +  api + url2 + filter
	# "/?format=json"
	# "/?format=api"

	#Concatenate the URL
	# Basic Y2hpbnRhbkA4ODQ4ZGlnaXRhbC5jb206QXJiQWtIZHdIQQ==
	# example outcome : http://admin:admin@192.168.112.1:5000/api/input/manufacturingorder/

	headers= {
		'Content-type': 'application/json; charset=UTF-8',
		'Authorization': frepple_settings.authorization_header,
	}
	print(url+ "-------------------------------------------------------------------------")

	return url,headers


def export_calendars():
	api = "calendar"
	url,headers = get_frepple_params(api=api,filter=None)

	calendars = frappe.db.sql(
		"""
		SELECT calendar_name,default_value 
		FROM `tabFrepple Calendar`""",
		as_dict=1
	)

	for calendar in calendars:
		data = json.dumps({
			"name": calendar.calendar_name,
			"defaultvalue":calendar.default_value
		})
		output = make_post_request(url,headers=headers, data=data)
	

def export_calendar_buckets():
	api = "calendarbucket"
	url,headers = get_frepple_params(api=api,filter=None)

	calendar_buckets = frappe.db.sql(
		"""
		SELECT calendar,value,priority, timestamp(start_datetime) as "start_datetime",timestamp(end_datetime) as "end_datetime",
		timestamp(start_time) as "start_time",timestamp(end_time) as "end_time",
		monday, tuesday, wednesday, thursday, friday, saturday, sunday
		FROM `tabFrepple Calendar Bucket`""",
		as_dict=1
	)

	for calendar_bucket in calendar_buckets:
		print(calendar_bucket)
		print(calendar_bucket.start_datetime.isoformat())
		data = json.dumps({
			"calendar": calendar_bucket.calendar,
			"startdate": calendar_bucket.start_datetime.isoformat(),
			"enddate":calendar_bucket.end_datetime.isoformat() ,
			"value": calendar_bucket.value,
			"priority": calendar_bucket.priority,
			"monday": "true" if calendar_bucket.monday else "false",
			"tuesday": "true" if calendar_bucket.tuesday else "false",
			"wednesday": "true" if calendar_bucket.wednesday else "false",
			"thursday": "true" if calendar_bucket.thursday else "false",
			"friday": "true" if calendar_bucket.friday else "false",
			"saturday": "true" if calendar_bucket.saturday else "false",
			"sunday": "true" if calendar_bucket.sunday else "false",
			"starttime": str(calendar_bucket.start_time.time()),
			"endtime":str(calendar_bucket.end_time.time())
		})
		output = make_post_request(url,headers=headers, data=data)
	

def export_items():
	api = "item" 
	print("fsgsdg")
	url,headers = get_frepple_params(api=api,filter=None)

	items = frappe.db.sql(
		"""
		SELECT item, description, stock_uom,category,subcategory,
		successor_part,shelf_life,type, valuation_rate, 
		item_group,weight,volume FROM `tabFrepple Item`""",
		as_dict=1)
	
	for item in items:
		print(item.shelf_life)
		'''Add the item_group to frepple to use it as the owner to ensure no request error happen'''
		data = json.dumps({
			"name": item.item_group
		})
		print(data)
		output = make_post_request(url,headers=headers, data=data)

		'''Add the actual item to frepple'''
		data = json.dumps({
			"name": item.item,
			"owner":item.item_group,
			"description":item.description,
			"uom":item.stock_uom,
			"cost":item.valuation_rate,
			"category":item.category,
			"shelflife":item.shelf_life,
			"subcategory":item.subcategory,
			"type":item.type,
			"volume":item.volume,
			"weight":item.weight,
			"successor":item.successor_part

		})
		output = make_post_request(url,headers=headers, data=data)
	

def export_customers():
	api = "customer"
	url,headers = get_frepple_params(api=api,filter=None)

	customers = frappe.db.sql("""SELECT name, customer_group, customer_type,category,subcategory FROM `tabFrepple Customer`""",as_dict=1)
	for customer in customers:
		'''Add the customer_group to frepple to use it as the owner to ensure no request error happen'''
		data = json.dumps({
			"name": customer.customer_group
		})
		output = make_post_request(url,headers=headers, data=data)

		'''Add the actual customer to frepple'''
		data = json.dumps({
			"name": customer.name,
			"category":customer.customer_type,
			"owner":customer.customer_group,
			"subcategory":customer.subcategory,
			"category":customer.category,

		})
		output = make_post_request(url,headers=headers, data=data)	


def export_locations():
	api = "location"
	url,headers = get_frepple_params(api=api,filter=None)

	locations = frappe.db.sql("""SELECT warehouse, location_owner, category,subcategory,description, available FROM `tabFrepple Location`""",as_dict=1)
	for location in locations:
	
		if location.available:
			available = location.available
		else:
			available = None

		# If the location is a child location
		if (location.location_owner != None):
			# Create the company document in frepple first
			data = json.dumps({
				"name": location.location_owner,
			})
			output = make_post_request(url,headers=headers, data=data)

			data = json.dumps({
				"name": location.warehouse,
				"available":available,
				"owner":location.location_owner, 
				# "subcategory":location.subcategory,
				# "category":location.category,
				# "descripiton":location.description
			})
			output = make_post_request(url,headers=headers, data=data)

		# If the location is a parent
		else:
			print(available)
			data = json.dumps({
				"name": location.warehouse,
				"available":available
			})
			output = make_post_request(url,headers=headers, data=data)
	

def export_buffers():
	api = "buffer"
	url,headers = get_frepple_params(api=api,filter=None)

	buffers = frappe.db.sql(
		"""
		SELECT item, location, onhand FROM `tabFrepple Buffer`
		""",
		as_dict=1)
	for buffer in buffers:
		data = json.dumps({
			"item":buffer.item,
			"location": buffer.location,
			"onhand": buffer.onhand,
		})
		output = make_post_request(url,headers=headers, data=data)
	

def export_item_distribution():
	api = "itemdistribution"
	url,headers = get_frepple_params(api=api,filter=None)
	distributions = frappe.db.sql(
		"""
		SELECT item,origin,destination,day,timestamp(time) as time,category,subcategory,batch,operation,policy,leadtime,
		description,req_shelf_life 
		FROM `tabFrepple Item Distribution`
		""",
	as_dict=1)

	for distribution in distributions:
		print(distribution.leadtime,11111)
		data = json.dumps({
			"item": distribution.item,
			"origin":distribution.origin,
			"location":distribution.destination,
			"leadtime":add_seconds_to_time(distribution.leadtime),
			
			# "source":distribution.operation,
			# "policy":distribution.policy,
			# "shelflife":distribution.req_shelf_life
		})
		output = make_post_request(url,headers=headers, data=data)


def export_resources():
	api = "resource" #equivalent to employee doctype
	url,headers = get_frepple_params(api=api,filter=None)
			
	resources = frappe.db.sql(
		"""
		SELECT name1, location,available, type, maximum,description,resource_owner ,subcategory,category,cost,efficiency
		FROM `tabFrepple Resource`
		""",as_dict=1)

	for resource in resources:
		print(resource)
	# For human resource
		'''Add a null operator or workstation to frepple to use it as the owner to ensure no request error happen'''
		data = json.dumps({
			"name": resource.resource_owner,#default
		})
		output = make_post_request(url,headers=headers, data=data)

		if resource.available:
			available = resource.available
		else:
			available = None
		
		'''Add the actual employee to frepple'''
		data = json.dumps({
			"name": resource.name1,
			"available":available,
			"type":resource.type,
			"maximum":resource.maximum,
			"description":resource.description,
			"location":resource.location,
			"owner":resource.resource_owner,
			"subcategory":resource.subcategory,
			"category":resource.category,
			"cost":resource.cost,
			"efficiency":resource.efficiency
		})
		output = make_post_request(url,headers=headers, data=data)
	

def export_skills():
	api = "skill" 
	url,headers = get_frepple_params(api=api,filter=None)

	skills = frappe.db.sql("""SELECT skill FROM `tabFrepple Skill`""",as_dict=1)
	for skill in skills:
		print(skill)
		data = json.dumps({
			"name": skill.skill,
		})

		output = make_post_request(url,headers=headers, data=data)


def export_resource_skills():
	api = "resourceskill" #equivalent to customer doctype
	url,headers = get_frepple_params(api=api,filter=None)
		
	employee_skill_list = frappe.db.sql("""SELECT resource,skill, proficiency FROM `tabFrepple Resource Skill`""",as_dict=1)
	
	for employee_skill in employee_skill_list:
		data = json.dumps({
			"resource": employee_skill.resource,
			"skill":employee_skill.skill,
			"priority":5-employee_skill.proficiency
		})

		output = make_post_request(url,headers=headers, data=data)

	
def export_suppliers():
	api = "supplier" #equivalent to customer doctype		
	url,headers = get_frepple_params(api=api,filter=None)
	

	suppliers = frappe.db.sql(
		"""
		SELECT supplier,description,subcategory,category
		FROM `tabFrepple Supplier`
		""",
	as_dict=1)
	for supplier in suppliers:
		data = json.dumps({
			"name": supplier.supplier,
			"description":supplier.description,
			"subcategory":supplier.subcategory,
			"category":supplier.category,
		})

		output = make_post_request(url,headers=headers, data=data)
		

def export_item_suppliers():
	api = "itemsupplier"
	url,headers = get_frepple_params(api=api,filter=None)
	item_suppliers = frappe.db.sql(
		"""
		SELECT supplier, item, supplier_cost, day, timestamp(time) as "time",Date(effective_end) as "effective_end",leadtime,
		Date(effective_start) as "effective_start" ,size_maximum,size_multiple,size_minimum,hard_safety_leadtime,extra_safety_leadtime
		FROM `tabFrepple Item Supplier`
		""",
	as_dict=1)
	
	#timestamp() sql method give us datetime type. So we can use datetime method time() to get time
	# date() to get date 

	for item_supplier in item_suppliers:
		# if item_supplier.time:
		# 	time = str(item_supplier.time.time())
		# else:
		# 	time = "null"

		print(item_supplier)
		# print(str(item_supplier.day)+" "+str(item_supplier.time.time()))
		data = json.dumps({
			"supplier":item_supplier.supplier,
			"item":item_supplier.item,
			"cost":item_supplier.supplier_cost,
		#	"leadtime":str(item_supplier.day)+" "+str(item_supplier.time.time()),
			"leadtime":add_seconds_to_time(item_supplier.leadtime),
			"sizeminimum":item_supplier.size_minimum,
			"sizemultiple":item_supplier.size_multiple,
			"sizemaximum":item_supplier.size_maximum,
			"hard_safety_leadtime":item_supplier.hard_safety_leadtime,
			"extra_safety_leadtime":item_supplier.extra_safety_leadtime,
			"effective_start":str(item_supplier.effective_start),
			"effective_end": str(item_supplier.effective_end)
			# "duration_per":(datetime(1900,1,1,0,0,0)+ operation.duration_per_unit).time(), 
		})

		output = make_post_request(url,headers=headers, data=data)
		

def export_operations():
	api = "operation"
	url,headers = get_frepple_params(api=api,filter=None)
	
	routing_operations = frappe.db.sql(
		"""
		SELECT operation, item, size_multiple,size_maximum
		size_minimum,Date(effective_end) as "effective_end",
		Date(effective_start) as "effective_start",search_mode,
		location, type, priority,per_unit_duration as "duration_per_unit",duration,operation_owner
		FROM `tabFrepple Operation`
		WHERE type = "routing"
		""",
		as_dict=1)
#timestamp(duration_per_unit) as "duration_per_unit", timestamp(duration) as "duration"
	print(routing_operations)
	for operation in routing_operations:
		print(operation)
		if operation.search_mode == 'priority':
			search_mode="PRIORITY" 
		elif operation.search_mode == 'minimum cost':
			search_mode=="MINCOST" 
		elif operation.search_mode =="minimum penalty":
			search_mode="MINPENALTY" 
		elif operation.search_mode =="minimum cost plus penalty":
			search_mode="MINCOSTPENALTY"
		if operation.search_mode:
			duration = operation.duration
		else:
			duration = None
		if operation.effective_start:
			start_date=str(operation.effective_start)
		else:
			start_date=None
		if operation.effective_end:
			end_date=str(operation.effective_end)
		else:
			end_date=None
		data = json.dumps({
			"name":operation.operation,
			"item":operation.item,
			"location":operation.location,
			"type":operation.type,
			"priority":operation.priority,
			# "duration_per":(datetime(1900,1,1,0,0,0)+ operation.duration_per_unit).time(), 
			"duration":add_seconds_to_time(duration),
			#"duration_per":add_seconds_to_time(operation.duration_per_unit),
			"sizeminimum":operation.size_minimum,
			"sizemultiple":operation.size_multiple,
			"sizemaximum":operation.size_maximum,
			"effective_start":start_date,
			"effective_end": end_date,
			"search":search_mode
			
		})
		
		output = make_post_request(url,headers=headers, data=data)
	
	time_per_operations = frappe.db.sql(
		"""
		SELECT operation, item, location, type, duration, duration_per_unit,priority,operation_owner
		FROM `tabFrepple Operation`
		WHERE type = "time_per"
		""",
	as_dict=1)#,timestamp(duration_per_unit) as "duration_per_unit", timestamp(duration) as "duration"
	
	for operation in time_per_operations:
		if operation.duration:
			duration =add_seconds_to_time(operation.duration)
		else:
			duration = None

		data = json.dumps({
			"name":operation.operation,
			"type":operation.type,
			"priority":operation.priority,
			"location":operation.location,
			# "duration_per":(datetime(1900,1,1,0,0,0)+ operation.duration_per_unit).time(), 
		#	"duration_per":add_seconds_to_time(operation.duration_per_unit),
			"duration":duration,
			"owner":operation.operation_owner
		})
		output = make_post_request(url,headers=headers, data=data)


def export_operation_materials():
	api = "operationmaterial"
	url,headers = get_frepple_params(api=api,filter=None)

	materials = frappe.db.sql(
		"""
		SELECT operation, item, quantity, type
		FROM `tabFrepple Operation Material`
		""",
	as_dict=1)
	
	for material in materials:
		print(material)
		data = json.dumps({
			"operation":material.operation,
			"item":material.item,
			"quantity":material.quantity,
			"type":material.type
		})
		output = make_post_request(url,headers=headers, data=data)


def export_operation_resources():
	api = "operationresource"
	url,headers = get_frepple_params(api=api,filter=None)

	employee_resources = frappe.db.sql(
		"""
		SELECT operation,employee_check,resource,quantity,skill 
		FROM `tabFrepple Operation Resource`
		WHERE employee_check = 1
		""",
	as_dict=1)

	for resource in employee_resources:
		print(resource)
		# if HUman Resource, then we let resource = "Operator"
		data = json.dumps({
			"operation":resource.operation,
			"resource":"Operator",
			"quantity":resource.quantity,
			"skill":resource.skill
		})
		output = make_post_request(url,headers=headers, data=data)

	workstation_resources = frappe.db.sql(
		"""
		SELECT operation,employee_check,resource,quantity 
		FROM `tabFrepple Operation Resource`
		WHERE employee_check = 0
		""",
	as_dict=1)

	for resource in workstation_resources:
		print(resource)
		data = json.dumps({
			"operation":resource.operation,
			"resource":resource.resource,
			"quantity":resource.quantity,
		})
		output = make_post_request(url,headers=headers, data=data)


def export_sales_orders():
	api = "demand" #equivalent sales order
	url,headers = get_frepple_params(api=api,filter=None)
	
	sales_orders = frappe.db.sql(
		"""
		SELECT name,item,item_name,qty,location,customer, timestamp(due) as "due",priority,status,so_owner
		FROM `tabFrepple Demand`
		""",
	as_dict=1)

		
	for sales_order in sales_orders:
		print(sales_order)
		data = json.dumps({
			"name": sales_order.name,
			"description": sales_order.item_name + " ordered by " + sales_order.customer, #default
			"item": sales_order.item,
			"customer": sales_order.customer,
			"location": sales_order.location,
			"due":  sales_order.due.isoformat(),
			"status": sales_order.status,
			"quantity": sales_order.qty,
			"priority": sales_order.priority
		})

		output = make_post_request(url,headers=headers, data=data)


@frappe.whitelist()
def get_frepple_params_for_forecast(api=None,filter=None):
	if not api:
		api = "" #default get the demand(=sales order in ERPNext) list from frepple
	if not filter:
		filter = ""

	frepple_settings = frappe.get_doc("Frepple Settings")
	temp_url = frepple_settings.url.split("//")
	end_point = "https://"+ frepple_settings.username + ":" + frepple_settings.password + "@" + temp_url[1] 
	url1=end_point + "/api/forecast/"
	url2 = "/"
	url = url1 +  api + url2 + filter
	headers= {
		'Content-type': 'application/json; charset=UTF-8',
		'Authorization': frepple_settings.authorization_header,
	}
	return url ,headers
	


@frappe.whitelist()
def export_frepple_forecast():
	api="forecast"
	url ,headers=get_frepple_params_for_forecast(api=api,filter=None)
	print(url,headers)
	forecast=frappe.db.sql(
		"""
		Select item,location,customer,forecast_method,planned,discrete,description,subcategory,
		category,priority,minimum_shipment,maximum_lateness,delivery_operation from `tabForecast`
		""",as_dict=1
	)
	for fc in forecast:
		if fc.forecast_method == 'Intermittent':
			forecast='intermittent'
		elif fc.forecast_method == 'Automatic':
			forecast='automatic'
		elif fc.forecast_method=='Constant':
			forecast='constant'
		elif fc.forecast_method == 'Trend':
			forecast='Trend'
		elif fc.forecast_method == 'Seasonal':
			forecast = 'seasonal'	
		data=json.dumps({
				"customer": fc.customer,
				"item": fc.item,
				"location":fc.location,
				"priority": fc.priority		
		})
		print(data)
		output = make_post_request(url,headers=headers, data=data)
		print(output) 
	

@frappe.whitelist()
def export_distribution_order():
	api = "distributionorder"
	url,headers = get_frepple_params(api=api,filter=None)

	distribution_orders = frappe.db.sql(
		"""
		SELECT 
		FROM `tabFrepple Operation Resource`
		Distribution Order
		""",
	as_dict=1)

	for order in distribution_orders:
		print(order)
		# if HUman Resource, then we let resource = "Operator"
		data = json.dumps({
			"item":order.item,
			"resource":"Operator",
			"quantity":order.quantity,
			"skill":order.skill
		})
		output = make_post_request(url,headers=headers, data=data)

	workstation_resources = frappe.db.sql(
		"""
		SELECT operation,employee_check,resource,quantity 
		FROM `tabFrepple Operation Resource`
		WHERE employee_check = 0
		""",
	as_dict=1)

	for resource in workstation_resources:
		print(resource)
		data = json.dumps({
			"operation":resource.operation,
			"resource":resource.resource,
			"quantity":resource.quantity,
		})
		output = make_post_request(url,headers=headers, data=data)


@frappe.whitelist()
def export_frepple_sub_operation():
	export_operations()
	api="suboperation"
	url,headers = get_frepple_params(api=api,filter=None)

	sub_operatiions = frappe.db.sql(
		"""
		SELECT operation,priority,suboperation,Date(effective_start) AS "effective_start" ,Date(effective_end) as "effective_end"
		FROM `tabFrepple Sub Operations`
		
		""",
	as_dict=1)

	for op in sub_operatiions:
		
		data = json.dumps({
        	"operation": op.operation,
			"suboperation": op.suboperation,
			"effective_start":str(op.effective_start),
			"effective_end":str(op.effective_end)
		})
		print(data)
		output = make_post_request(url,headers=headers, data=data)
		

@frappe.whitelist()
def export_frepple_operation_dependencies():
	export_operations()
	api="operationdependency"
	url,headers = get_frepple_params(api=api,filter=None)
	sub_operatiions = frappe.db.sql(
		"""
		SELECT operation,blocked_by_operation,quantity,soft_safety_lead_time ,hard_safety_lead_time
		FROM `tabFrepple Operation Dependencies`
		
		""",
	as_dict=1)

	for op in sub_operatiions:
		
		data = json.dumps({
        	"operation": op.operation,
			"blockedby": op.blocked_by_operation,
			"quantity":op.quantity,
			"safety_leadtime":op.soft_safety_lead_time,
			"hard_safety_leadtime":op.hard_safety_leadtime,
			# "duration":add_seconds_to_time(op.duration),
			# "duration_per":add_seconds_to_time(op.duration_per_unit),
		})
		print(data)
		output = make_post_request(url,headers=headers, data=data)
		

def export_resource_detail():
	api="operationplanresource"
	url,headers = get_frepple_params(api=api,filter=None)
	resource_detail=frappe.db.sql(
		"""
		SELECT resource,quantity
		FROM `tabFrepple Resource Detail`
		""",as_dict=1)
	for rd in resource_detail:
		data= json.dumps({
			"resource":rd.get('resource'),
			"quantity":rd.get('quantity')	
		})
		output = make_post_request(url,headers=headers, data=data)
		


from datetime import timedelta

def add_seconds_to_time(seconds):
	delta = timedelta(seconds=seconds)
	days = delta.days
	time_str = str(delta - timedelta(days=days))
	return f"{days} {time_str}"