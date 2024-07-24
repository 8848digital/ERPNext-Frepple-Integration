# -*- coding: utf-8 -*-
# Copyright (c) 2022, Drayang Chua and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe,json
from frappe.model.document import Document

class FreppleItemSupplier(Document):
	pass

@frappe.whitelist()
def generate_erp_party_specific_item(**kwargs):
	item_supplier_doc=json.loads(kwargs.get('doc'))
	party_speific_doc=frappe.new_doc('Party Specific Item')
	party_speific_doc.party_type='Supplier'
	party_speific_doc.party=item_supplier_doc.get('supplier')
	party_speific_doc.based_on_value=item_supplier_doc.get('item')
	party_speific_doc.save()
	return party_speific_doc.name

@frappe.whitelist()
def bulk_update_party_specific_record(**kwargs):
	item_supplier_record = json.loads(kwargs['names'])
	for record in item_supplier_record:
		supplier , item = frappe.db.get_value('Frepple Item Supplier',record,['supplier','item'])
		party_speific_doc=frappe.new_doc('Party Specific Item')
		party_speific_doc.party_type = 'Supplier'
		party_speific_doc.party = supplier
		party_speific_doc.based_on_value = item
		party_speific_doc.save()
