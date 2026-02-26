-- Migration: Ajout du statut de livraison à transfer_history
ALTER TABLE transfer_history
ADD COLUMN delivery_status ENUM('non_envoye', 'envoye', 'echec') DEFAULT 'non_envoye' AFTER status,
ADD COLUMN delivery_message TEXT AFTER delivery_status;
