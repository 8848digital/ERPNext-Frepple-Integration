frappe.listview_settings['Frepple Item Supplier'] = {
    onload(listview) {
        listview.page.add_action_item('Export to ErpNext', 
            () => 
            listview.call_for_selected_items("frepple.frepple.doctype.frepple_item_supplier.frepple_item_supplier.bulk_update_party_specific_record")
        );
    }
}