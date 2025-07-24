# Production Database Table Schemas

This document contains the actual column schemas for all critical tables in the production Supabase database.

## 1. invoices
| Column Name | Data Type | Nullable | Default | Max Length |
|-------------|-----------|----------|---------|------------|
| invoice_id | integer | NO | nextval('invoices_invoice_id_seq'::regclass) | - |
| order_id | integer | NO | - | - |
| invoice_number | character varying | NO | - | 50 |
| invoice_date | date | NO | - | - |
| customer_id | integer | NO | - | - |
| customer_name | character varying | NO | - | 200 |
| customer_gstin | character varying | YES | - | 15 |
| billing_address | text | NO | - | - |
| shipping_address | text | YES | - | - |
| subtotal_amount | numeric | NO | - | - |
| discount_amount | numeric | YES | 0 | - |
| taxable_amount | numeric | NO | - | - |
| cgst_amount | numeric | YES | 0 | - |
| sgst_amount | numeric | YES | 0 | - |
| igst_amount | numeric | YES | 0 | - |
| total_tax_amount | numeric | NO | - | - |
| round_off_amount | numeric | YES | 0 | - |
| total_amount | numeric | NO | - | - |
| payment_status | character varying | YES | 'unpaid'::character varying | 20 |
| paid_amount | numeric | YES | 0 | - |
| payment_date | timestamp without time zone | YES | - | - |
| payment_method | character varying | YES | - | 50 |
| invoice_type | character varying | YES | 'tax_invoice'::character varying | 20 |
| notes | text | YES | - | - |
| created_at | timestamp without time zone | YES | CURRENT_TIMESTAMP | - |
| created_by | integer | YES | - | - |
| org_id | uuid | NO | - | - |
| due_date | date | YES | (CURRENT_DATE + '30 days'::interval) | - |
| invoice_status | character varying | YES | 'generated'::character varying | 20 |
| updated_at | timestamp without time zone | YES | CURRENT_TIMESTAMP | - |
| cancelled_at | timestamp without time zone | YES | - | - |
| cancellation_reason | text | YES | - | - |
| pdf_url | text | YES | - | - |
| pdf_generated_at | timestamp without time zone | YES | - | - |
| billing_name | character varying | NO | ''::character varying | 200 |
| billing_city | character varying | NO | ''::character varying | 100 |
| billing_state | character varying | NO | ''::character varying | 100 |
| billing_pincode | character varying | NO | ''::character varying | 10 |
| gst_type | character varying | NO | 'cgst_sgst'::character varying | 20 |
| place_of_supply | character varying | NO | '09'::character varying | 2 |

## 2. invoice_payments
| Column Name | Data Type | Nullable | Default | Max Length |
|-------------|-----------|----------|---------|------------|
| payment_id | integer | NO | nextval('invoice_payments_payment_id_seq'::regclass) | - |
| invoice_id | integer | NO | - | - |
| payment_date | date | NO | - | - |
| amount | numeric | NO | - | - |
| payment_mode | character varying | NO | - | 20 |
| transaction_reference | character varying | YES | - | 100 |
| bank_name | character varying | YES | - | 100 |
| cheque_number | character varying | YES | - | 50 |
| cheque_date | date | YES | - | - |
| notes | text | YES | - | - |
| created_at | timestamp without time zone | YES | CURRENT_TIMESTAMP | - |
| payment_amount | numeric | NO | 0 | - |
| payment_reference | character varying | NO | - | 50 |
| status | character varying | YES | 'completed'::character varying | 20 |
| updated_at | timestamp without time zone | YES | CURRENT_TIMESTAMP | - |
| created_by | integer | YES | - | - |
| cancellation_reason | text | YES | - | - |
| cancelled_at | timestamp without time zone | YES | - | - |

## 3. orders
| Column Name | Data Type | Nullable | Default | Max Length |
|-------------|-----------|----------|---------|------------|
| order_id | integer | NO | nextval('orders_order_id_seq'::regclass) | - |
| org_id | uuid | YES | - | - |
| order_number | text | NO | - | - |
| order_date | date | NO | CURRENT_DATE | - |
| order_time | time without time zone | YES | CURRENT_TIME | - |
| customer_id | integer | NO | - | - |
| customer_name | text | YES | - | - |
| customer_phone | text | YES | - | - |
| subtotal_amount | numeric | YES | 0 | - |
| discount_amount | numeric | YES | 0 | - |
| tax_amount | numeric | YES | 0 | - |
| round_off_amount | numeric | YES | 0 | - |
| final_amount | numeric | YES | 0 | - |
| payment_mode | text | YES | 'cash'::text | - |
| payment_status | text | YES | 'pending'::text | - |
| paid_amount | numeric | YES | 0 | - |
| balance_amount | numeric | YES | 0 | - |
| invoice_number | text | YES | - | - |
| invoice_date | date | YES | - | - |
| payment_due_date | date | YES | - | - |
| delivery_type | text | YES | 'pickup'::text | - |
| delivery_address | text | YES | - | - |
| delivery_status | text | YES | 'pending'::text | - |
| delivered_date | date | YES | - | - |
| order_status | text | YES | 'pending'::text | - |
| branch_id | integer | YES | - | - |
| created_by | integer | YES | - | - |
| approved_by | integer | YES | - | - |
| notes | text | YES | - | - |
| tags | ARRAY | YES | - | - |
| created_at | timestamp with time zone | YES | CURRENT_TIMESTAMP | - |
| updated_at | timestamp with time zone | YES | CURRENT_TIMESTAMP | - |
| prescription_required | boolean | YES | false | - |
| prescription_id | integer | YES | - | - |
| doctor_id | integer | YES | - | - |
| is_urgent | boolean | YES | false | - |
| delivery_slot | text | YES | - | - |
| loyalty_points_earned | integer | YES | 0 | - |
| loyalty_points_redeemed | integer | YES | 0 | - |
| applied_scheme_id | integer | YES | - | - |
| delivery_date | date | YES | - | - |
| order_type | character varying | YES | 'sales'::character varying | 20 |
| payment_terms | character varying | YES | 'credit'::character varying | 20 |
| delivery_charges | numeric | YES | 0 | - |
| other_charges | numeric | YES | 0 | - |
| billing_name | character varying | YES | - | 200 |
| billing_address | character varying | YES | - | 500 |
| billing_gstin | character varying | YES | - | 20 |
| shipping_name | character varying | YES | - | 200 |
| shipping_address | character varying | YES | - | 500 |
| shipping_phone | character varying | YES | - | 15 |
| confirmed_at | timestamp without time zone | YES | - | - |
| delivered_at | timestamp without time zone | YES | - | - |
| delivery_notes | text | YES | - | - |

## 4. order_items
| Column Name | Data Type | Nullable | Default | Max Length |
|-------------|-----------|----------|---------|------------|
| order_item_id | integer | NO | nextval('order_items_order_item_id_seq'::regclass) | - |
| order_id | integer | NO | - | - |
| product_id | integer | NO | - | - |
| product_name | text | YES | - | - |
| batch_id | integer | YES | - | - |
| batch_number | text | YES | - | - |
| expiry_date | date | YES | - | - |
| quantity | integer | NO | - | - |
| uom_code | text | YES | - | - |
| base_quantity | integer | YES | - | - |
| mrp | numeric | YES | - | - |
| selling_price | numeric | NO | - | - |
| discount_percent | numeric | YES | 0 | - |
| discount_amount | numeric | YES | 0 | - |
| tax_percent | numeric | YES | - | - |
| tax_amount | numeric | YES | - | - |
| total_price | numeric | NO | - | - |
| item_status | text | YES | 'active'::text | - |
| notes | text | YES | - | - |
| created_at | timestamp with time zone | YES | CURRENT_TIMESTAMP | - |
| unit_price | numeric | NO | 0 | - |
| line_total | numeric | YES | 0 | - |
| updated_at | timestamp without time zone | YES | CURRENT_TIMESTAMP | - |

## 5. customers
| Column Name | Data Type | Nullable | Default | Max Length |
|-------------|-----------|----------|---------|------------|
| customer_id | integer | NO | nextval('customers_customer_id_seq'::regclass) | - |
| org_id | uuid | YES | - | - |
| customer_code | text | NO | - | - |
| customer_name | text | NO | - | - |
| customer_type | text | YES | 'retail'::text | - |
| business_type | text | YES | - | - |
| phone | text | YES | - | - |
| alternate_phone | text | YES | - | - |
| email | text | YES | - | - |
| address | text | YES | - | - |
| city | text | YES | - | - |
| state | text | YES | - | - |
| pincode | text | YES | - | - |
| landmark | text | YES | - | - |
| gst_number | text | YES | - | - |
| pan_number | text | YES | - | - |
| drug_license_number | text | YES | - | - |
| food_license_number | text | YES | - | - |
| credit_limit | numeric | YES | 0 | - |
| credit_period_days | integer | YES | 0 | - |
| payment_terms | text | YES | - | - |
| price_list_id | integer | YES | - | - |
| discount_percent | numeric | YES | 0 | - |
| assigned_sales_rep | integer | YES | - | - |
| customer_group | text | YES | - | - |
| loyalty_points | integer | YES | 0 | - |
| total_business | numeric | YES | 0 | - |
| outstanding_amount | numeric | YES | 0 | - |
| last_order_date | date | YES | - | - |
| order_count | integer | YES | 0 | - |
| is_active | boolean | YES | true | - |
| blacklisted | boolean | YES | false | - |
| blacklist_reason | text | YES | - | - |
| created_by | integer | YES | - | - |
| created_at | timestamp with time zone | YES | CURRENT_TIMESTAMP | - |
| updated_at | timestamp with time zone | YES | CURRENT_TIMESTAMP | - |
| customer_category | text | YES | - | - |
| monthly_potential | numeric | YES | - | - |
| preferred_payment_mode | text | YES | - | - |
| collection_route | text | YES | - | - |
| visiting_days | ARRAY | YES | - | - |
| contact_person | character varying | YES | - | 100 |
| address_line1 | character varying | YES | - | 200 |
| address_line2 | character varying | YES | - | 200 |
| gstin | character varying | YES | - | 20 |
| credit_days | integer | YES | 0 | - |
| notes | text | YES | - | - |
| area | text | YES | - | - |
| state_code | character varying | YES | - | 2 |

## 6. products
[Truncated for brevity - contains all product fields including pack_input, pack_quantity, etc.]

## 7. batches
[Truncated for brevity - contains all batch fields for inventory management]

---

**Note**: This schema was captured on 2025-07-24 from the production Supabase database. Any schema changes should update this document accordingly.