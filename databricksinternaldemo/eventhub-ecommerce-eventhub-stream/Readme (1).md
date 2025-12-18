
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/4df9e58f-8569-48cf-85e8-c7e7439707a6" />


E-COMMERCE EVENT STREAMING PIPELINE
High-Level Documentation

📋 Executive Summary
Built a complete end-to-end data pipeline that ingests e-commerce order events from Azure Event Hub, processes them through a medallion architecture (Bronze/Silver/Gold), and creates business intelligence dashboards—all using Unity Catalog in Databricks.
Key Achievement: Production-ready data pipeline from event generation to business dashboards in 7 notebooks + 8 materialized views.

🎯 Business Problem
Challenge: Process real-time e-commerce order events and transform them into actionable business insights.
Requirements:

Ingest streaming e-commerce events (orders with product details)
Normalize data for data quality
Enrich data for analytics
Create business aggregations
Enable self-service BI dashboards

📦 What We Built
Core Pipeline (7 Notebooks)
NotebookPurposeOutputTime00_Config.pySetup Unity Catalog schemas, Event Hub config3 schemas created30s01_Data_Generator.pyGenerate & send 300 order eventsEvents in Event Hub60s02_Bronze_Layer.pyRead events, split into orders & products2 Bronze tables2m03_Silver_Layer.pyJOIN orders with products1 Silver table1m04_Gold_Layer.pyCreate business aggregations4 Gold tables2m05_Materialized_Views.pyCreate optimized views8 MVs30s06_Genie_Dashboards.pySetup Genie AI queriesGenie configs30s07_SQL_Dashboards.pyCreate SQL dashboard queries10 queries30s
Total Execution Time: ~8 minutes

🗄️ Data Model
Bronze Layer (Normalized)
orders (300 records)
├─ order_id (PK)  
├─ customer_id  
├─ product_id (FK) ──┐  
├─ quantity          │  
├─ total_amount      │  
└─ timestamps        │  
                     │  
products (10 records)│  
├─ product_id (PK) ◄─┘  
├─ product_name
├─ brand  
├─ category  
└─ base_price  
Silver Layer (Enriched)  
order_details (300 records)  
├─ All order fields  
├─ All product fields (joined)  
└─ Calculated fields (order_date, order_hour, etc.)  
Gold Layer (Aggregated)  
1. sales_by_brand_category
   - Revenue, orders, customers by brand & category

2. location_performance  
   - Revenue, customers, delivery rate by city

3. product_performance
   - Sales, quantity, discounts by product

4. customer_insights
   - Spending, behavior, segmentation by customer
Materialized Views (8)
mv_top_brands              - Brand rankings
mv_category_summary        - Category metrics
mv_location_ranking        - Location rankings
mv_product_ranking         - Product rankings
mv_customer_segments       - Customer tiers
mv_vip_customers          - Top customers
mv_brand_location_matrix  - Cross-analysis
mv_discount_analysis      - Discount impact

🔑 Key Technical Decisions
1. Direct Table Creation (Not Streaming)
Why: Simpler, more reliable

Used EventHubConsumerClient (Python SDK)
Batch processing instead of Spark Structured Streaming
Direct .saveAsTable() to Unity Catalog
No intermediate file paths
Easier to debug and maintain

Trade-off: Not real-time, but good for batch loads

2. Kafka Connector Approach (Alternative)
Why: Avoids Event Hub library compatibility issues

Event Hub is Kafka-compatible
spark-sql-kafka-0-10 is built into Databricks
No Maven library installation needed
No Scala version conflicts

Status: Implemented but simplified to direct SDK approach

3. Unity Catalog Native
Why: Governance, sharing, security

All tables in Unity Catalog
Proper data governance
Easy to share across teams
Catalog: na-dbxtraining
Schemas: biju_bronze, biju_silver, biju_gold


4. Enriched Event Pattern
Why: Efficient data distribution

Single event contains order + product data
Split in Bronze for normalization
Rejoin in Silver for analytics
Reduces Event Hub partitions needed

Event Structure:
json{
  "order_id": "ORD000001",
  "customer_id": "C1023",
  "quantity": 2,
  "total_amount": 2400.00,
  "product_id": "P001",
  "product_name": "Laptop",
  "brand": "Dell",
  "category": "Electronics"
}

5. Materialized Views for Performance
Why: Fast dashboard queries

Pre-aggregated metrics
Optimized for BI tools
Can be scheduled to refresh
Reduces query time from seconds to milliseconds


🎨 Dashboard Options
Option 1: Genie (AI-Powered) ⭐ Recommended

Natural language queries
"Show me top 5 brands by revenue"
AI-generated visualizations
Self-service for business users
Setup: 5 pre-configured spaces

Option 2: SQL Dashboards (Traditional)

Standard SQL queries
Fixed visualizations (bar, pie, table)
Familiar for SQL users
Setup: 10 ready-to-use queries


📊 Business Metrics Available
Sales Metrics

Total Revenue
Revenue by Brand
Revenue by Category
Revenue by Location
Average Order Value

Product Metrics

Top Products by Sales
Product Performance by Category
Discount Effectiveness
Revenue per Unit
Product Popularity

Customer Metrics

Customer Segmentation (High/Medium/Low Value)
Customer Lifetime Value
VIP Customers
Purchase Patterns
Brand Affinity

Operational Metrics

Order Count
Delivery Rate by Location
Items Sold
Discount Impact


🔐 Security & Configuration
Azure Integration

Event Hub: evhns-natraining.servicebus.windows.net
Event Hub Name: evh-natraining-biju
Key Vault: dbx-ss-kv-natraining-2
Secret: evh-natraining-read-write

Unity Catalog

Catalog: na-dbxtraining  
Bronze Schema: biju_bronze  
Silver Schema: biju_silver  
Gold Schema: biju_gold  
