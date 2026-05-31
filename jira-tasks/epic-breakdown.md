---
projectKey: "SCRUM" 
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
inputDocuments:
  - d:\workspace\new-bmad\_bmad-output\planning-artifacts\prds\prd-todo-list-2026-05-27\prd.md
  - d:\workspace\new-bmad\_bmad-output\planning-artifacts\architecture.md
  - d:\workspace\new-bmad\_bmad-output\planning-artifacts\ux-designs\ux-todo-list-2026-05-27\DESIGN.md
  - d:\workspace\new-bmad\_bmad-output\planning-artifacts\ux-designs\ux-todo-list-2026-05-27\EXPERIENCE.md
---

# todo-list - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for todo-list, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Người dùng có thể tạo công việc mới với tiêu đề và tùy chọn mô tả.
FR2: Người dùng có thể sửa tiêu đề, mô tả và trạng thái công việc.
FR3: Người dùng có thể xóa công việc.
FR4: Người dùng có thể đánh dấu công việc là hoàn thành hoặc chưa hoàn thành.
FR5: Danh sách công việc hiển thị trạng thái hoàn thành rõ ràng.
FR6: Danh sách công việc có thể lọc theo tất cả, chưa hoàn thành, đã hoàn thành.
FR7: Danh sách công việc có thể sắp xếp theo ngày tạo và mức ưu tiên (nếu có).
FR8: Người dùng có thể đặt nhắc nhở cho công việc.
FR9: Ứng dụng có thể đồng bộ dữ liệu công việc với backend đơn giản nếu cần.
FR10: Ứng dụng chạy trên trình duyệt web hiện đại.
FR11: Dữ liệu cá nhân được lưu để người dùng không mất công việc khi làm mới trang.

### NonFunctional Requirements

NFR1: Giao diện phải tải và phản hồi nhanh trong vòng 1-2 giây khi mở trang.
NFR2: Giao diện trực quan, dễ dùng với mức độ tối giản.
NFR3: Dữ liệu người dùng được lưu an toàn, không yêu cầu đăng nhập phiên bản đầu tiên.
NFR4: Thiết kế phù hợp với desktop và có thể hoạt động trên mobile cơ bản.

### Additional Requirements

- Starter template được chọn là Vite + React + TypeScript và khởi tạo bằng `npm create vite@latest todo-list -- --template react-ts`.
- Ứng dụng ưu tiên frontend-first với state management nhẹ và không cần server-side rendering cho phiên bản đầu tiên.
- Dữ liệu người dùng nên được lưu trong `localStorage` trên trình duyệt và có khả năng mở rộng sang backend sync trong tương lai.
- Kiến trúc cần tách rõ layer UI và persistence để dễ mở rộng.
- Data model todo nên bao gồm `id`, `title`, `description`, `createdAt`, `completed`, `priority`, và `dueDate` tùy chọn.
- Styling MVP có thể dùng CSS module hoặc plain CSS, áp dụng design tokens từ UX.
- Deployment cho phiên bản đầu là static hosting, build bằng Vite.
- Cần đảm bảo responsiveness và accessibility ở mức tối thiểu.

### UX Design Requirements

UX-DR1: Áp dụng hệ thống màu sắc và typography token theo spec, bao gồm màu primary, accent, surface, background, neutral, text, success, danger.
UX-DR2: Xây dựng các component UI tái sử dụng: primary/secondary/text button, filled input, task card với status badge, empty state illustration/prompt.
UX-DR3: Thiết kế layout cột đơn responsive với spacing và bo góc nhất quán theo design tokens.
UX-DR4: Task card phải hiển thị rõ ràng tiêu đề, mô tả tóm tắt, trạng thái, và các hành động hoàn thành, sửa, xóa.
UX-DR5: Form thêm task phải có input tiêu đề bắt buộc, mô tả tùy chọn và nút Thêm rõ ràng; khi không có task hiển thị empty state thân thiện.
UX-DR6: Cung cấp điều khiển lọc All / Active / Completed và sorting theo ngày tạo hoặc priority.
UX-DR7: Đảm bảo accessibility cơ bản: tương phản 4.5:1, kích thước nhấn tối thiểu 44x44px, nhãn rõ ràng cho input và button, hỗ trợ điều hướng bàn phím.
UX-DR8: Cài đặt các trạng thái tương tác: thêm task, hoàn thành task, sửa task, xóa task, lọc cập nhật ngay, empty/completed state hiển thị rõ.

### FR Coverage Map

FR1: Epic 1 - Enable users to create new tasks with title and optional description.
FR2: Epic 1 - Enable users to edit task content and status.
FR3: Epic 1 - Enable users to remove tasks they no longer need.
FR4: Epic 1 - Enable users to mark tasks complete or incomplete.
FR5: Epic 1 - Ensure task list clearly shows completed status.
FR6: Epic 2 - Allow users to filter task list by completion state.
FR7: Epic 2 - Allow users to sort tasks by creation date and priority.
FR8: Epic 2 - Allow users to set reminders for tasks.
FR9: Epic 3 - Allow tasks to sync with a backend when enabled.
FR10: Epic 3 - Ensure the app runs in a modern browser environment.
FR11: Epic 3 - Persist user tasks across page refreshes.

## Epic List

### Epic 1: Core Task Management
Deliver a working personal todo experience where users can add, update, remove, and complete tasks in a clear list.
**FRs covered:** FR1, FR2, FR3, FR4, FR5

### Epic 2: Task Organization, Reminders, and Views
Provide filtering, sorting, and reminder controls so users can focus on active tasks and keep important work top of mind.
**FRs covered:** FR6, FR7, FR8

### Epic 3: Reliable Persistence and Sync
Make the todo application fast, accessible, responsive, and optionally synchronized so users can trust it across sessions and devices.
**FRs covered:** FR9, FR10, FR11

## Epic 1: Core Task Management

Deliver a working personal todo experience where users can add, update, remove, and complete tasks in a clear list.

### Story 1.1: Initialize the project with Vite + React + TypeScript

As a developer,
I want to set up the initial project using the selected Vite + React + TypeScript starter,
So that the codebase is ready for building the todo application.

**Acceptance Criteria:**

**Given** the Architecture document specifies Vite + React + TypeScript as the starter,
**When** I run the starter setup command,
**Then** the project scaffolding is created in a `todo-list` folder,
**And** the project includes the standard Vite React TypeScript files and can start with `npm install` and `npm run dev`.

### Story 1.2: Create a new task

As a user,
I want to add a new task with a title and optional description,
So that I can capture the work I need to do.