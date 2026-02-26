-- Migration : Ajout du champ api_url à la table partner_university
ALTER TABLE partner_university ADD COLUMN api_url VARCHAR(512) AFTER country;