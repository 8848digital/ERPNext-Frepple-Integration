import json
import os
import frappe


def after_uninstall():
	remove_custom_fields()


def remove_custom_fields():
	CUSTOM_FIELDS = {}
	print("Removing Custom Fields....")
	path = os.path.join(os.path.dirname(__file__), "frepple/custom_field")
	for file in os.listdir(path):
		with open(os.path.join(path, file), "r") as f:
			CUSTOM_FIELDS.update(json.load(f))

	for doctype, fields in CUSTOM_FIELDS.items():
		for field in fields:
			fieldname = field["fieldname"]
			custom_field_name = f"{doctype}-{fieldname}"
			try:
				frappe.delete_doc("Custom Field", custom_field_name)
				frappe.db.commit()
				print(f"Custom field {fieldname} removed from {doctype} successfully.")
			except frappe.DoesNotExistError:
				print(f"Custom field {fieldname} does not exist in {doctype}.")
			except Exception as e:
				print(
					f"An error occurred while removing custom field {fieldname} from {doctype}: {e}"
				)
