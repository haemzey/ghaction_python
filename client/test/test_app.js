import { beforeEach, describe, expect, it, vi } from "vitest";
import fs from "fs";
import path from "path";
import { JSDOM } from "jsdom";


// ============================================================
// Test data
// ============================================================

const books = [
    {
        id: 1,
        title: "The Linux Command Line",
        author: "William Shotts",
        isbn: "9781593279523",
        category: "Linux",
        published_year: 2019,
        total_copies: 3,
        available_copies: 2,
    },
    {
        id: 2,
        title: "Docker Deep Dive",
        author: "Nigel Poulton",
        isbn: "9781916585258",
        category: "Docker",
        published_year: 2023,
        total_copies: 2,
        available_copies: 2,
    },
];

const members = [
    {
        id: 1,
        name: "Hamza",
        email: "hamza@example.com",
        phone: "03001234567",
        active: 1,
    },
    {
        id: 2,
        name: "Ali",
        email: "ali@example.com",
        phone: null,
        active: 0,
    },
];

const loans = [
    {
        id: 1,
        book_id: 1,
        member_id: 1,
        book_title: "The Linux Command Line",
        member_name: "Hamza",
        member_email: "hamza@example.com",
        due_date: "2026-09-25",
        returned_at: null,
    },
    {
        id: 2,
        book_id: 2,
        member_id: 2,
        book_title: "Docker Deep Dive",
        member_name: "Ali",
        member_email: "ali@example.com",
        due_date: "2026-09-01",
        returned_at: "2026-09-05T10:00:00+00:00",
    },
];

const stats = {
    books: 2,
    available_copies: 4,
    active_loans: 1,
    active_members: 1,
};


// ============================================================
// DOM setup
// ============================================================

function createDOM() {
    const html = `
    < !DOCTYPE html >
        <html>
            <body>

                <div id="alert" class="hidden"></div>

                <h1 id="page-title"></h1>

                <div id="books-section" class="page-section"></div>
                <div id="members-section" class="page-section"></div>
                <div id="loans-section" class="page-section"></div>

                <div id="overview-section" class="page-section"></div>

                <div id="books-table"></div>
                <div id="members-table"></div>
                <div id="loans-table"></div>
                <div id="recent-loans"></div>
                <div id="collection-list"></div>

                <input id="book-search" value="">
                    <select id="category-filter">
                        <option value="">All categories</option>
                    </select>

                    <select id="loan-filter">
                        <option value="">All</option>
                        <option value="true">Active</option>
                        <option value="false">Returned</option>
                    </select>

                    <select id="loan-book"></select>
                    <select id="loan-member"></select>

                    <div id="total-books"></div>
                    <div id="available-copies"></div>
                    <div id="active-loans"></div>
                    <div id="active-members"></div>

                    <button id="refresh-btn"></button>

                    <form id="book-form"></form>
                    <form id="member-form"></form>
                    <form id="loan-form"></form>

            </body>
        </html>
`;

    const dom = new JSDOM(html, {
        url: "http://localhost",
        runScripts: "outside-only",
    });

    global.window = dom.window;
    global.document = dom.window.document;
    global.FormData = dom.window.FormData;

    return dom;
}


// ============================================================
// Mock API
// ============================================================

function mockFetch() {
    global.fetch = vi.fn((url) => {
        const responses = {
            "/api/stats": {
                status: 200,
                json: async () => stats,
            },

            "/api/books": {
                status: 200,
                json: async () => ({
                    books,
                    count: books.length,
                }),
            },

            "/api/members": {
                status: 200,
                json: async () => ({
                    members,
                    count: members.length,
                }),
            },

            "/api/loans": {
                status: 200,
                json: async () => ({
                    loans,
                    count: loans.length,
                }),
            },
        };

        const response = responses[url];

        if (!response) {
            return Promise.resolve({
                status: 404,
                ok: false,
                json: async () => ({
                    error: "Not found",
                }),
            });
        }

        return Promise.resolve({
            ok: response.status >= 200 && response.status < 300,
            status: response.status,
            json: response.json,
        });
    });
}


// ============================================================
// Import application
// ============================================================

async function loadApplication() {
    /*
     * script.js currently executes immediately when imported.
     *
     * Vitest resets the module before each test so the application
     * can be loaded against our fresh DOM.
     */

    vi.resetModules();

    await import("../script.js");
}


// ============================================================
// Test setup
// ============================================================

beforeEach(() => {
    vi.clearAllMocks();

    createDOM();

    mockFetch();
});


// ============================================================
// API tests
// ============================================================

describe("API function", () => {

    it("loads application data from the backend", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        expect(fetch).toHaveBeenCalledWith(
            "/api/stats",
            expect.objectContaining({
                headers: {
                    "Content-Type": "application/json",
                },
            }),
        );

        expect(fetch).toHaveBeenCalledWith(
            "/api/books",
            expect.objectContaining({
                headers: {
                    "Content-Type": "application/json",
                },
            }),
        );

        expect(fetch).toHaveBeenCalledWith(
            "/api/members",
            expect.objectContaining({
                headers: {
                    "Content-Type": "application/json",
                },
            }),
        );

        expect(fetch).toHaveBeenCalledWith(
            "/api/loans",
            expect.objectContaining({
                headers: {
                    "Content-Type": "application/json",
                },
            }),
        );
    });
});


// ============================================================
// Data loading tests
// ============================================================

describe("loadData", () => {

    it("loads statistics into the dashboard", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        expect(
            document.querySelector("#total-books").textContent
        ).toBe("2");

        expect(
            document.querySelector("#available-copies").textContent
        ).toBe("4");

        expect(
            document.querySelector("#active-loans").textContent
        ).toBe("1");

        expect(
            document.querySelector("#active-members").textContent
        ).toBe("1");
    });


    it("loads book categories into the category filter", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const categoryFilter =
            document.querySelector("#category-filter");

        expect(categoryFilter.innerHTML).toContain("Linux");
        expect(categoryFilter.innerHTML).toContain("Docker");
    });


    it("loads available books into loan book select", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const loanBook =
            document.querySelector("#loan-book");

        expect(loanBook.innerHTML).toContain(
            "The Linux Command Line"
        );

        expect(loanBook.innerHTML).toContain(
            "Docker Deep Dive"
        );
    });


    it("loads active members into loan member select", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const loanMember =
            document.querySelector("#loan-member");

        expect(loanMember.innerHTML).toContain("Hamza");
        expect(loanMember.innerHTML).not.toContain("Ali");
    });
});


// ============================================================
// Book rendering tests
// ============================================================

describe("renderBooks", () => {

    it("renders books in the books table", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const table =
            document.querySelector("#books-table");

        expect(table.innerHTML).toContain(
            "The Linux Command Line"
        );

        expect(table.innerHTML).toContain(
            "Docker Deep Dive"
        );
    });


    it("filters books by search text", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const search =
            document.querySelector("#book-search");

        search.value = "docker";

        search.dispatchEvent(
            new window.Event("input")
        );

        const table =
            document.querySelector("#books-table");

        expect(table.innerHTML).toContain(
            "Docker Deep Dive"
        );

        expect(table.innerHTML).not.toContain(
            "The Linux Command Line"
        );
    });


    it("filters books by category", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const category =
            document.querySelector("#category-filter");

        category.value = "Docker";

        category.dispatchEvent(
            new window.Event("change")
        );

        const table =
            document.querySelector("#books-table");

        expect(table.innerHTML).toContain(
            "Docker Deep Dive"
        );

        expect(table.innerHTML).not.toContain(
            "The Linux Command Line"
        );
    });
});


// ============================================================
// Member rendering tests
// ============================================================

describe("renderMembers", () => {

    it("renders members", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const table =
            document.querySelector("#members-table");

        expect(table.innerHTML).toContain("Hamza");
        expect(table.innerHTML).toContain(
            "hamza@example.com"
        );

        expect(table.innerHTML).toContain("Ali");
        expect(table.innerHTML).toContain(
            "ali@example.com"
        );
    });


    it("renders active and inactive member status", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const table =
            document.querySelector("#members-table");

        expect(table.innerHTML).toContain("Active");
        expect(table.innerHTML).toContain("Inactive");
    });
});


// ============================================================
// Loan rendering tests
// ============================================================

describe("renderLoans", () => {

    it("renders loans", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const table =
            document.querySelector("#loans-table");

        expect(table.innerHTML).toContain(
            "The Linux Command Line"
        );

        expect(table.innerHTML).toContain(
            "Docker Deep Dive"
        );
    });


    it("shows active and returned loan status", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const table =
            document.querySelector("#loans-table");

        expect(table.innerHTML).toContain("Active");
        expect(table.innerHTML).toContain("Returned");
    });


    it("shows return button only for active loans", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const buttons =
            document.querySelectorAll(".return-loan");

        expect(buttons.length).toBe(1);
        expect(buttons[0].dataset.id).toBe("1");
    });


    it("filters active loans", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const filter =
            document.querySelector("#loan-filter");

        filter.value = "true";

        filter.dispatchEvent(
            new window.Event("change")
        );

        const table =
            document.querySelector("#loans-table");

        expect(table.innerHTML).toContain(
            "The Linux Command Line"
        );

        expect(table.innerHTML).not.toContain(
            "Docker Deep Dive"
        );
    });


    it("filters returned loans", async () => {
        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const filter =
            document.querySelector("#loan-filter");

        filter.value = "false";

        filter.dispatchEvent(
            new window.Event("change")
        );

        const table =
            document.querySelector("#loans-table");

        expect(table.innerHTML).toContain(
            "Docker Deep Dive"
        );

        expect(table.innerHTML).not.toContain(
            "The Linux Command Line"
        );
    });
});


// ============================================================
// Error handling
// ============================================================

describe("error handling", () => {

    it("shows backend API errors", async () => {

        global.fetch = vi.fn(() =>
            Promise.resolve({
                ok: false,
                status: 500,
                json: async () => ({
                    error: "Database unavailable",
                }),
            })
        );

        await loadApplication();

        await new Promise((resolve) => setTimeout(resolve, 0));

        const alert =
            document.querySelector("#alert");

        expect(alert.textContent).toBe(
            "Database unavailable"
        );

        expect(alert.classList.contains("hidden"))
            .toBe(false);
    });
});
