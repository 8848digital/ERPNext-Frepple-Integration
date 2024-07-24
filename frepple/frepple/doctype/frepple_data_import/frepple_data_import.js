// Copyright (c) 2024, Drayang Chua and contributors
// For license information, please see license.txt

frappe.ui.form.on("Frepple Data Import", {
	refresh(frm) {

	},
    get_data_from_frepple(frm){
		frm.call({
			method:"import_data",
			args:{
				doc: frm.doc
			},
			callback:function(r){
				console.log(r.message)
			},
		})
	},
});
