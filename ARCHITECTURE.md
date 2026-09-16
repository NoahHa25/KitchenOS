# KitchenOS — System Architecture

> **Status:** Living document
> **Last updated:** 2026-09-16
> **Current phase:** Sprint 3 — Recipes & Food Cost

---

## 1. Overview

KitchenOS is a restaurant operations platform designed to manage ingredients, inventory, recipes, food costs, and eventually provide intelligent forecasting and operational insights.

The system is being built around a simple principle:

> **Operational data should become the foundation for automation and intelligence.**

Inventory is not treated as a simple CRUD resource. Stock changes are represented as transactional movements so that the system can answer not only:

- "How much stock do we have?"

but also:

- "Why did the stock change?"
- "When did it change?"
- "What operation caused it?"
- "What should the stock level be after this operation?"

Recipes extend this model by connecting dishes to ingredients and quantities.

This creates the foundation for automatic ingredient consumption and food-cost calculation.

---

# 2. Current Architecture

The backend currently follows a layered architecture:

```text
┌─────────────────────────────┐
│          Client             │
│   Web / Mobile / Admin UI   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│        FastAPI API          │
│      Routes / Schemas       │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│          Services           │
│      Business Logic         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│        Repositories         │
│       Data Access Layer     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         PostgreSQL          │
│       Persistent Data       │
└─────────────────────────────┘
```

### Architectural rule

API routes should not contain domain logic.

The intended flow is:

```text
HTTP Request
    ↓
Router
    ↓
Service
    ↓
Repository
    ↓
Database
```

Business rules belong in services.

Database access belongs in repositories.

API concerns belong in routers and schemas.

---

# 3. Technology Stack

## Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Pydantic

## API Documentation

FastAPI provides OpenAPI/Swagger documentation for the backend API.

## Database

PostgreSQL is the primary relational database.

Alembic manages schema migrations.

---

# 4. Multi-Tenant Architecture

KitchenOS is designed around restaurant-level data isolation.

The conceptual hierarchy is:

```text
Platform
   │
   └── Restaurant
         │
         ├── Ingredients
         ├── Inventory
         ├── Stock Movements
         ├── Recipes
         └── Recipe Ingredients
```

Restaurant-owned data must always be scoped to the appropriate restaurant.

The system should never rely on the frontend to enforce tenant isolation.

Tenant boundaries are enforced at the backend/data-access layer.

---

# 5. Inventory Domain

Inventory is one of the core domains of KitchenOS.

The current system contains the concept of:

```text
Ingredient
    │
    └── Inventory Stock
            │
            └── Stock Movements
```

An ingredient represents a material used by the restaurant.

Examples:

```text
Tomato
Mozzarella
Basil
Olive Oil
```

Inventory represents the current quantity available.

Stock movements represent changes to that quantity.

---

# 6. Stock Movement Ledger

Stock changes are represented through explicit movements.

Supported movement concepts include:

- Purchase
- Usage
- Waste
- Adjustment

Conceptually:

```text
Purchase
    ↓
+ Stock

Usage
    ↓
- Stock

Waste
    ↓
- Stock

Adjustment
    ↓
± Stock
```

The movement ledger provides an auditable history of inventory changes.

Instead of silently modifying stock, an operation should produce a corresponding movement record.

---

# 7. Transactional Inventory Updates

Inventory mutations are transactional.

For example:

```text
BEGIN TRANSACTION

1. Validate operation
2. Read current stock
3. Calculate new quantity
4. Update inventory
5. Create stock movement
6. Commit

COMMIT
```

If any required step fails:

```text
ROLLBACK
```

This prevents situations where the inventory quantity changes but the corresponding movement record is missing.

The inventory quantity and its movement record should therefore remain consistent.

---

# 8. Numeric Precision

Inventory quantities use database numeric types rather than floating-point representations.

Application-level calculations use Python `Decimal`.

This is important for quantities such as:

```text
0.20 kg
0.15 kg
0.01 kg
0.02 L
```

Food-cost calculations will also depend on precise decimal arithmetic.

Floating-point arithmetic should not be used for financial or quantity calculations where exact decimal representation matters.

---

# 9. Database Migrations

Database schema changes are managed through Alembic.

The migration history is part of the application's source of truth.

Schema changes should follow:

```text
Model Change
     ↓
Alembic Migration
     ↓
Migration Applied
     ↓
Application Updated
```

Migrations should be committed together with the application changes they support.

---

# 10. Base Model Ownership

The project currently uses:

```text
app/models/base.py
```

as the canonical location for the SQLAlchemy declarative `Base`.

An old:

```text
app/db/base.py
```

file was introduced during an earlier circular-import fix and is no longer required.

### Sprint 3 cleanup

Remove the unused:

```text
app/db/base.py
```

and keep a single canonical `Base`.

The goal is to avoid multiple competing sources of truth for model configuration.

---

# 11. Recipe Domain

Sprint 3 introduces recipes.

A recipe describes how a menu item is produced.

Conceptually:

```text
Recipe
   │
   ├── Ingredient A
   │      └── Quantity
   │
   ├── Ingredient B
   │      └── Quantity
   │
   └── Ingredient C
          └── Quantity
```

For example:

```text
Margherita Pizza

Tomato       0.20 kg
Mozzarella   0.15 kg
Basil        0.01 kg
Olive Oil    0.02 L
```

---

# 12. Recipe Data Model

Sprint 3 introduces two primary tables:

```text
recipes
recipe_ingredients
```

Conceptually:

```text
recipes
-------
id
restaurant_id
name
description
...

        │
        │ 1:N
        ▼

recipe_ingredients
------------------
id
recipe_id
ingredient_id
quantity
...
```

The relationship is:

```text
Recipe
  │
  └── RecipeIngredient
          │
          └── Ingredient
```

A recipe can contain many ingredients.

An ingredient can be used in many recipes.

The `recipe_ingredients` table represents the relationship and stores the required quantity.

---

# 13. Recipe → Inventory Relationship

Recipes connect menu production with inventory consumption.

Example:

```text
Margherita Pizza
       │
       ├── Tomato       0.20 kg
       ├── Mozzarella   0.15 kg
       ├── Basil        0.01 kg
       └── Olive Oil    0.02 L
```

When one pizza is produced/sold, the system can calculate:

```text
Required Tomato     = 0.20 kg
Required Mozzarella = 0.15 kg
Required Basil      = 0.01 kg
Required Olive Oil  = 0.02 L
```

These requirements can then be translated into inventory usage movements.

---

# 14. Food Cost

Recipe ingredients provide the data required to calculate food cost.

Conceptually:

```text
Ingredient Cost
      ×
Recipe Quantity
      =
Recipe Ingredient Cost
```

Then:

```text
Food Cost
=
Σ all recipe ingredient costs
```

For example:

```text
Tomato       → quantity × current cost
Mozzarella   → quantity × current cost
Basil        → quantity × current cost
Olive Oil    → quantity × current cost

                    ↓

              Total Food Cost
```

The food-cost engine should use precise decimal arithmetic.

---

# 15. Future Sales Flow

The intended future flow is:

```text
Menu Item Sold
      ↓
Recipe Loaded
      ↓
Recipe Ingredients Loaded
      ↓
Required Quantities Calculated
      ↓
Inventory Validated
      ↓
Inventory Updated
      ↓
Usage Movements Created
      ↓
Food Cost Calculated
      ↓
Low Stock Rules Evaluated
```

This is one of the central architectural goals of KitchenOS.

---

# 16. Low Stock Detection

Ingredients may have a minimum stock threshold.

Conceptually:

```text
Current Stock < Minimum Stock
             ↓
        Low Stock Alert
```

Initially this can be a deterministic rule.

Later it can become an input into forecasting and recommendation systems.

---

# 17. AI / Forecasting Direction

The inventory and recipe domains are intentionally being built before the AI layer.

The long-term data flow is:

```text
Sales
  ↓
Recipes
  ↓
Ingredient Consumption
  ↓
Inventory History
  ↓
Historical Demand
  ↓
Forecasting
  ↓
Purchase Recommendations
```

This creates a clean separation between:

### Operational system

Responsible for:

- recipes
- inventory
- stock movements
- costs
- restaurant data

and:

### Intelligence layer

Responsible for:

- demand forecasting
- anomaly detection
- purchasing recommendations
- waste prediction
- operational insights

The AI layer should consume reliable operational data rather than becoming responsible for basic inventory correctness.

---

# 18. Architectural Principles

## 18.1 Business logic belongs in services

Routes should remain thin.

Bad:

```text
Router
 ├── database queries
 ├── calculations
 ├── validation
 └── business rules
```

Preferred:

```text
Router
   ↓
Service
   ↓
Repository
```

---

## 18.2 Database access belongs in repositories

Repositories provide an abstraction around persistence.

Services should not need to know unnecessary database implementation details.

---

## 18.3 Mutations must be auditable

Important operational changes should produce explicit records.

Inventory is therefore modeled as both:

```text
Current State
+
Historical Events
```

---

## 18.4 Financial calculations require precision

Costs and quantities should use decimal-safe representations.

---

## 18.5 Tenant isolation is mandatory

Every restaurant must operate inside its own data boundary.

Cross-restaurant data access must never happen accidentally.

---

## 18.6 Schema changes are versioned

Database changes must be represented by migrations.

---

# 19. Current Development Status

### Completed

- FastAPI backend foundation
- PostgreSQL integration
- SQLAlchemy models
- Alembic migrations
- Restaurant-scoped architecture
- Ingredient domain
- Inventory domain
- Stock movement ledger
- Transactional inventory updates
- Decimal-safe quantity handling
- Purchase / usage / waste / adjustment operations

### Current Sprint

**Sprint 3 — Recipes & Food Cost**

Planned:

- Architecture documentation
- Remove obsolete `app/db/base.py`
- Recipe model
- Recipe ingredient model
- Recipe CRUD
- Recipe validation
- Food-cost calculation
- Recipe-driven inventory consumption
- Low-stock integration

---

# 20. Architectural Roadmap

```text
                    KitchenOS
                       │
        ┌──────────────┴──────────────┐
        │                             │
   Operations                    Intelligence
        │                             │
        ▼                             ▼
 Ingredients                    Forecasting
 Inventory                      Recommendations
 Recipes                        Anomaly Detection
 Stock Movements                 Waste Prediction
 Food Cost                      Insights
        │                             │
        └──────────────┬──────────────┘
                       ▼
                Restaurant OS
```

The operational foundation comes first.

The intelligence layer is built on top of it.

---

# 21. Decision Record

KitchenOS favors:

- explicit domain models
- transactional state changes
- auditable ledgers
- decimal-safe quantities and costs
- service/repository separation
- restaurant-level tenant isolation
- migration-driven schema evolution

These decisions are intended to keep the system understandable while it grows from an MVP into a production-oriented restaurant platform.
