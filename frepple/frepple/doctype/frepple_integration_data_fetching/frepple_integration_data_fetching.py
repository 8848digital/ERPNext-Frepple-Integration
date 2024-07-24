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

class FreppleIntegrationDataFetching(Document):
	pass

@frappe.whitelist()
def fetch_data(doc):
	doc = json.loads(doc)

	import_datas = []
	# Sales
	if doc["frepple_item"]:
		fetch_items()
		import_datas.append("Frepple Item")
	if doc["frepple_customer"]:
		fetch_customers()
		import_datas.append("Frepple Customer")
	if doc["frepple_location"]:
		fetch_locations()
		import_datas.append("Frepple Location")

	# Inventory
	if doc["frepple_buffer"]:
		fetch_buffers()
	# if doc["frepple_item_distribution"]:
		# fetch_item_distribution()


	# Capacity
	if doc["frepple_resource"]:
		fetch_resources()
		import_datas.append("Frepple Resource")
	if doc["frepple_skill"]:
		fetch_skills()
		import_datas.append("Frepple Skill")
	# HAVENT include yet
	if doc["frepple_resource_skill"]:
		fetch_resource_skills()
		import_datas.append("Frepple Resource Skill")

	# Purchasing
	if doc["frepple_supplier"]:
		fetch_suppliers()
		import_datas.append("Frepple Supplier")
	# if doc["frepple_item_supplier"]:
	# 	fetch_item_suppliers()
	# 	import_datas.append("Frepple Item Supplier")
	
	# Manufacturing
	if doc["frepple_operation"]:
		fetch_operations()
		import_datas.append("Frepple Operation")
	if doc["frepple_operation_material"]:
		fetch_operation_materials()
		import_datas.append("Frepple Operation Materials")

	if doc["frepple_operation_resource"]:
		fetch_operation_resources()
		import_datas.append("Frepple Operation Resource")

	if doc["frepple_demand"]:
		fetch_sales_orders()
		import_datas.append("Frepple Demand")

	# Output msg 
	for import_data in import_datas:
		frappe.msgprint(_("{0} is imported.").format(import_data))



def fetch_items():
	items = frappe.db.sql("""SELECT item_code, item_name, item_group, valuation_rate, stock_uom FROM `tabItem`""",as_dict=1)
	for item in items:
		if not frappe.db.exists("Frepple Item",item.item_code):
			new_item = frappe.new_doc("Frepple Item")
			new_item.item = item.item_code
			new_item.description = item.item_name
			new_item.uom = item.stock_uom
			new_item.cost = item.valuation_rate
			new_item.item_owner = item.item_group
			new_item.insert()
		else:#Update 
			frappe.db.set_value('Frepple Item', item.item_code, {
				'valuation_rate':item.valuation_rate,
			}) 

def fetch_customers():
	customers = frappe.db.sql("""SELECT name, customer_group, customer_type FROM `tabCustomer`""",as_dict=1)
	for customer in customers:
		if not frappe.db.exists("Frepple Customer",customer.name):
			new_customer = frappe.new_doc("Frepple Customer")
			new_customer.customer = customer.name
			new_customer.customer_group = customer.customer_group
			new_customer.customer_type = customer.customer_type
			new_customer.insert()

def fetch_locations():
	locations = frappe.db.sql("""SELECT name, company FROM `tabWarehouse`""",as_dict=1)
	companys = frappe.db.sql("""SELECT name FROM `tabCompany`""",as_dict = 1)
	
	for company in companys:
		if not frappe.db.exists("Frepple Location",company.name):
			new_location = frappe.new_doc("Frepple Location")
			new_location.warehouse = company.name
			new_location.insert()
	for location in locations:
		if not frappe.db.exists("Frepple Location",location.name):
			new_location = frappe.new_doc("Frepple Location")
			new_location.warehouse = location.name
			new_location.location_owner = location.company
			new_location.insert()

def fetch_buffers():
	bins = frappe.db.sql(
		"""
		SELECT 
		warehouse, item_code,actual_qty 
		FROM `tabBin`
		""",
		as_dict=1)
	for bin in bins:
		if not frappe.db.exists("Frepple Buffer",bin.item_code+"@"+bin.warehouse):
			new_bin = frappe.new_doc("Frepple Buffer")
			new_bin.item = bin.item_code
			new_bin.location = bin.warehouse
			new_bin.onhand = bin.actual_qty
			new_bin.insert()
		else: #update
			frappe.db.set_value('Frepple Buffer',bin.item_code+"@"+bin.warehouse, {
				'onhand':bin.actual_qty,
			}) #Update the quantity


def fetch_resources():
	employees = frappe.db.sql("""SELECT name, employee_name FROM `tabEmployee`""",as_dict=1)
	locations = frappe.db.sql(
	"""
	SELECT name FROM `tabFrepple Location`
	WHERE name LIKE 'Work In Progress%%'
	""",
	as_dict=1)
	for employee in employees:
		if not frappe.db.exists("Frepple Resource",employee.name):
			new_employee = frappe.new_doc("Frepple Resource")
			new_employee.employee = employee.name
			new_employee.description = employee.employee_name
			new_employee.location = locations[0].name
			new_employee.resource_owner = "Operator" #default

			new_employee.name1 = employee.name
			new_employee.employee_check = 1
			new_employee.insert()
	
	# workstations = frappe.db.sql("""SELECT ws.name, fl.name FROM `tabWorkstation` ws, `tabFrepple Location` fl""",as_dict=1)
	workstations = frappe.db.sql(
		"""
		SELECT name FROM `tabWorkstation`
		""",
		as_dict=1)
	for workstation in workstations:
		if not frappe.db.exists("Frepple Resource",workstation.name):
			new_workstation = frappe.new_doc("Frepple Resource")
			new_workstation.workstation = workstation.name
			new_workstation.location = locations[0].name
			new_workstation.resource_owner = "Workstation" #default

			new_workstation.name1 = workstation.name
			new_workstation.workstation_check = 1
			new_workstation.insert()

def fetch_skills():
	skills = frappe.db.sql("""SELECT name FROM `tabSkill`""",as_dict=1)
	for skill in skills:
		if not frappe.db.exists("Frepple Skill",skill.name):
			new_skill = frappe.new_doc("Frepple Skill")
			new_skill.skill = skill.name
			new_skill.insert()


def fetch_resource_skills():
	employee_skill_list = frappe.db.sql("""
		SELECT esm.name, es.skill, es.proficiency
		FROM `tabEmployee Skill Map` esm, `tabEmployee Skill` es
		WHERE esm.name = es.parent
		""",
	as_dict=1)

	if (employee_skill_list):
		for i in employee_skill_list:
			print(i)
			
			if not frappe.db.exists("Frepple Resource Skill",i.name+"@"+i.skill):
				new_resource_skill = frappe.new_doc("Frepple Resource Skill")
				new_resource_skill.skill = i.skill
				new_resource_skill.resource = i.name
				new_resource_skill.proficiency = i.proficiency
				new_resource_skill.insert()
			elif frappe.db.exists("Frepple Resource Skill",i.name+"@"+i.skill):
				frappe.db.set_value('Frepple Resource Skill',i.name+"@"+i.skill, {
					'proficiency':i.proficiency
				}) 

def fetch_suppliers():
	suppliers = frappe.db.sql("""SELECT name FROM `tabSupplier`""",as_dict=1)
	for supplier in suppliers:
		if not frappe.db.exists("Frepple Supplier",supplier.name):
			new_supplier = frappe.new_doc("Frepple Supplier")
			new_supplier.supplier = supplier.name
			new_supplier.insert()

''' Not necessary'''
# def fetch_supplier_items():
# 	suppliers = frappe.db.sql("""SELECT name FROM `tabSupplier`""",as_dict=1)
# 	for supplier in suppliers:
# 		if not frappe.db.exists("Frepple Supplier",supplier.name):
# 			new_supplier = frappe.new_doc("Frepple Supplier")
# 			new_supplier.supplier = supplier.name
# 			new_supplier.insert()


# def fetch_operations():
# 	locations = frappe.db.sql(
# 		"""
# 		SELECT name FROM `tabFrepple Location`
# 		WHERE name LIKE 'Work In Progress%%'
# 		""",
# 		as_dict=1)
# 	BOMs = frappe.db.sql(
# 		"""
# 		SELECT bom.name,bom.item, bom.is_active, bom.is_default, bomop.operation, bomop.workstation,bomop.idx, bomop.time_in_mins,bomit.item_code 
# 		FROM `tabBOM` bom, `tabBOM Operation` bomop,`tabBOM Item` bomit
# 		WHERE bom.is_active = 1 and bom.is_default and bom.name = bomop.parent and bom.name = bomit.parent
# 		""",
# 		as_dict=1)
	
# 	for BOM in BOMs:
# 		if not frappe.db.exists("Frepple Operation",BOM.name): 
# 			# FOR routing type operation : BOM
# 			print(BOM)
# 			new_operation = frappe.new_doc("Frepple Operation")
# 			new_operation.operation = BOM.name
# 			new_operation.location = locations[0].name
# 			new_operation.type = "routing"
# 			new_operation.item = BOM.item
# 			new_operation.duration = 0
# 			new_operation.priority = 1
# 			new_operation.insert()
		

# 		if not frappe.db.exists("Frepple Operation",BOM.operation+"@"+BOM.name):
# 			# For time per type operation : Operation in the BOM
# 			new_operation = frappe.new_doc("Frepple Operation")
# 			new_operation.operation = BOM.operation+"@"+BOM.name
# 			new_operation.location = locations[0].name
# 			new_operation.type = "time_per"
# 			new_operation.operation_owner = BOM.name
# 			new_operation.duration = 0
# 			new_operation.duration_per_unit=0 #get only the time
# 			new_operation.priority = BOM.idx
# 			new_operation.insert()
# 		else:
# 			continue
# 			frappe.db.set_value('Frepple Operation', BOM.operation+"@"+BOM.name, {
# 				'duration_per_unit':add_to_date(datetime(1900,1,1,0,0,0),minutes=(BOM.time_in_mins),as_datetime=True).time() #get only the time,
# 			}) 


def fetch_operations():
		operation = frappe.db.sql("""
		Select * from `tabOperation`
		""",as_dict=True)		
		for op in operation:
			print(type(op.duration) ,op.duration,type(op.duration_per),op.duration_per)
			if not frappe.db.exists("Frepple Operation", {'operation':op.name,"item":op.item}):
				new_operation = frappe.new_doc("Frepple Operation")
				new_operation.operation = op.name
				new_operation.location = op.location
				#new_operation.type = op.type
				new_operation.operation_owner = op.name
				new_operation.duration = op.duration
				new_operation.duration_per_unit= op.duration_per
				new_operation.priority = op.priority
				new_operation.item = op.item
				new_operation.insert()
			else:
				continue
				frappe.db.set_value('Frepple Operation', BOM.operation+"@"+BOM.name, {
					'duration_per_unit':add_to_date(datetime(1900,1,1,0,0,0),minutes=(BOM.time_in_mins),as_datetime=True).time() #get only the time,
				}) 

# def fetch_operation_materials():
# 	BOMs = frappe.db.sql(
# 		"""
# 		SELECT bom.name, bom.item,bom.quantity, bom.transfer_material_against, bom.is_active, bom.is_default,bomop.operation,bomit.item_code,bomit.qty 
# 		FROM `tabBOM` bom, `tabBOM Operation` bomop,`tabBOM Item` bomit
# 		WHERE bom.is_active = 1 and bom.is_default=1 and bom.name = bomop.parent and bom.name = bomit.parent
# 		""",
# 	as_dict=1)

# 	for BOM in BOMs:
# 		print(BOM.name)
# 		frepple_operations = frappe.db.sql(
# 			"""
# 			SELECT name,type,operation_owner
# 			FROM `tabFrepple Operation`
# 			WHERE type = "time_per" and operation_owner = %s
# 			""",
# 		BOM.name,as_dict=1)
# 		print(frepple_operations[0].name)
# 		if (BOM.transfer_material_against == "Work Order"): #let the first operation consumed raw material and produce product
# 			# for item in BOM.item_code:
# 			# For product which is being produced
# 			if not frappe.db.exists("Frepple Operation Material",BOM.item+"-"+frepple_operations[0].name):
# 				new_operation_material = frappe.new_doc("Frepple Operation Material")
# 				new_operation_material.operation = frepple_operations[0].name
# 				new_operation_material.item = BOM.item
# 				new_operation_material.type = "end"
# 				new_operation_material.quantity = BOM.quantity
				
# 				new_operation_material.insert()

# 			# For raw materials which is being consumed
# 			if not frappe.db.exists("Frepple Operation Material",BOM.item_code+"-"+frepple_operations[0].name):
# 				new_operation_material = frappe.new_doc("Frepple Operation Material")
# 				new_operation_material.operation = frepple_operations[0].name
# 				new_operation_material.item = BOM.item_code
# 				new_operation_material.type = "start"
# 				new_operation_material.quantity = BOM.qty * -1 #consumed item need to be negative
# 				new_operation_material.insert()


# 	''' NOT YET CONSIDER the case if material transfer type is "JOB card" where each operation got their own type'''
# 		# if (BOM.transfer_material_against == "Job Card"): #assign material to the correspond operation

# 		# if not frappe.db.exists("Frepple Operation",BOM.operation+"@"+BOM.name):
# 		# 	new_operation = frappe.new_doc("Frepple Operation")
# 		# 	new_operation.operation = BOM.operation+"@"+BOM.name
# 		# 	new_operation.location = locations[0].name
# 		# 	new_operation.type = "time_per"
# 		# 	new_operation.operation_owner = BOM.name
# 		# 	new_operation.duration = time(0,0,0)
# 		# 	new_operation.duration_per_unit=add_to_date(datetime(1900,1,1,0,0,0),minutes=(BOM.time_in_mins),as_datetime=True).time() #get only the time
# 		# 	new_operation.insert()


# def fetch_operation_resources():
# 	BOMs = frappe.db.sql(
# 		"""
# 		SELECT bom.name, bom.is_active, bom.is_default, bomop.operation, bomop.workstation 
# 		FROM `tabBOM` bom, `tabBOM Operation` bomop
# 		WHERE bom.is_active = 1 and bom.is_default=1 and bomop.parent = bom.name
# 		""",
# 	as_dict=1)


# 	for BOM in BOMs:
# 		if not frappe.db.exists("Frepple Operation Resource",BOM.workstation+"-"+BOM.operation+"@"+BOM.name):
# 			new_doc = frappe.new_doc("Frepple Operation Resource")
# 			new_doc.operation = BOM.operation+"@"+BOM.name
# 			new_doc.resource = BOM.workstation
# 			if frappe.db.exists("Frepple Resource",BOM.workstation) and frappe.db.exists("Frepple Operation",BOM.operation+"@"+BOM.name):
# 				new_doc.insert()

def fetch_operation_resources():
	boms = frappe.db.get_all('BOM',pluck='name')
	for bom_op in boms:
		bom_op_rec = frappe.db.get_all('BOM Operation',filters={'parent':bom_op},fields=['*'])
		print(len(bom_op_rec))
		for rec in bom_op_rec:
			print(f"{rec.operation}-{rec.workstation}","$$$$$$$$$$$$$$$$$$$$$$$$$$$")
			if not frappe.db.exists('Frepple Operation Resource',{'name':f"{rec.workstation}-{rec.operation}"}):
				print("#######################")
				op_rec_doc = frappe.new_doc('Frepple Operation Resource')
				op_rec_doc.operation = rec.operation
				op_rec_doc.resource = rec.workstation
				op_rec_doc.or_owner = rec.parent
				op_rec_doc.save()
			else:
				continue


	# for BOM in BOMs:
	# 	if not frappe.db.exists("Frepple Operation Resource",BOM.workstation+"-"+BOM.operation+"@"+BOM.name):
	# 		new_doc = frappe.new_doc("Frepple Operation Resource")
	# 		new_doc.operation = BOM.operation+"@"+BOM.name
	# 		new_doc.resource = BOM.workstation
	# 		if frappe.db.exists("Frepple Resource",BOM.workstation) and frappe.db.exists("Frepple Operation",BOM.operation+"@"+BOM.name):
	# 			new_doc.insert()

def fetch_operation_materials():
	boms = frappe.db.get_all('BOM',pluck='name')
	for bom_op in boms:
		bom_items = frappe.db.get_all('BOM Explosion Item',filters={'parent':bom_op},fields=['*'])
		for rec in bom_items:
			if not frappe.db.exists('Frepple Operation Material',{'item':rec.item_code}):
				op_rec_doc = frappe.new_doc('Frepple Operation Material')
				op_rec_doc.operation = rec.operation
				op_rec_doc.item = rec.item_code
				op_rec_doc.type = 'start'
				op_rec_doc.quantity = -rec.qty_consumed_per_unit
				op_rec_doc.save()
			else:
				continue
		doc = frappe.get_doc('BOM',bom_op)
		bom_op_record = frappe.new_doc('Frepple Operation Material')
		bom_op_record.item = doc.item
		bom_op_record.quantity = doc.quantity + 1
		bom_op_record.operation = doc.custom_operation_to_manufacture
		bom_op_record.type = 'end'
		bom_op_record.save()

def fetch_sales_orders():
	sales_orders = frappe.db.sql(
		"""
		SELECT so.name, so.company, so.status,so.docstatus, soi.delivery_date, so.customer,soi.item_code, soi.qty, soi.work_order_qty  
		FROM `tabSales Order` so, `tabSales Order Item` soi
		WHERE soi.parent = so.name and soi.work_order_qty < 1 and so.docstatus = 1
		""",
	as_dict=1)

	locations = frappe.db.sql(
		"""
		SELECT name FROM `tabFrepple Location`
		WHERE name LIKE 'Work In Progress%%'
		""",
	as_dict=1)
		
	for sales_order in sales_orders:
		frepple_demands = frappe.db.sql(
			"""
			SELECT name  
			FROM `tabFrepple Demand`
			WHERE name like %s 
			""",
		(sales_order.name+'%'), as_dict=1)

		deliver_date = sales_order.delivery_date
		# Check the delivery date is none or not
		if sales_order.delivery_date == None:
			deliver_date= add_to_date(datetime.now(),days=(4),as_datetime=True).date() #set a default date 4 day after today
		
		# CHeck the erpnext sales order status and get its correspond frepple demand status
		status = so_status_e2f(sales_order.status)
		
		if not len(frepple_demands): #If we have more than 1 element in the array, mean the demand already existed
			new_demand = frappe.new_doc("Frepple Demand")
			new_demand.item = sales_order.item_code
			new_demand.qty = sales_order.qty
			# new_demand.location = sales_order.company #Cannot use company because in frepple, demand lcoation MUST 
														# as the operation lcoation
			new_demand.location = locations[0].name
			new_demand.customer = sales_order.customer
			new_demand.due =  datetime.combine(deliver_date,time(0,0,0))
			new_demand.so_owner =  sales_order.name
			new_demand.status = status
			new_demand.insert()
		else: #update
			for frepple_demand in frepple_demands:
				frappe.db.set_value('Frepple Demand',frepple_demand.name, {
					'status':status
				}) 

# CHeck the erpnext sales order status and get its correspond frepple demand status
# ERPnext to frepple
def so_status_e2f(status):
	switcher={
		"Draft":'inquiry',
		"On Hold":'inquiry',
		"To Deliver and Bill":'open',
		"To Bill":'closed',
		"To Deliver":'closed',
		"Completed":'closed',
		"Cancelled":'canceled',
		"Closed":'closed',
		"Overdue": 'canceled',
		}
	return switcher.get(status,"inquiry")

	'ERPNext'				'Frepple'
	# Draft					inquiry
	# On Hold				quote
	# To Deliver and Bill	open
	# To Bill				closed
	# To Deliver			cancelled
	# Completed
	# Cancelled
	# Closed
