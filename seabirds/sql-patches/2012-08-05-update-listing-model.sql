BEGIN;
ALTER TABLE cms_listing RENAME primary_list to optional_list; 
COMMIT;
