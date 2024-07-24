// Copyright (c) 2022, Drayang Chua and contributors
// For license information, please see license.txt

frappe.ui.form.on('Frepple Item Supplier', {
	refresh: function(frm) {
		frm.add_custom_button(__('Export to ERPNext'), function() {
			frm.call({
				method:"generate_erp_party_specific_item",
				args:{
					doc: frm.doc
				},
				callback:function(r){
					if (r.message){
						frappe.msgprint('Record Mapped Successfully')
					}
				},
			})
		});
	}
});
