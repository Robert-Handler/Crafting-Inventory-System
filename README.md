
# Crafting Inventory & Project Tracking System

This project is a microservices-based crafting management application built for CS 361.  
Its goal is to help users track crafting inventory (yarn, fabric, tools, etc.), manage ongoing and planned projects, and generate shopping lists automatically.

The architecture follows a microservices approach required by the course:  
- A **main program** (CLI or GUI) that communicates with  
- Multiple **independent microservices** running in separate processes.

---

## 📌 Features (Planned and Implemented)
- Track crafting inventory (materials, quantities, units)
- Look up materials by barcode/SKU
- Create and manage craft projects
- Track project status: planned, in-progress, completed
- Generate shopping lists based on inventory shortages
- Search, sort, and filter inventory
- Store pattern metadata (links, files, notes)
- Secure login/logout system
- Unit conversions (yards ↔ meters, grams ↔ ounces)
