# Design and Plan for Custom Data Extraction Forms

This document outlines the plan for implementing flexible, project-specific data extraction forms.

Related document: For authentication, roles, and permissions across projects, see RBAC Rules and Workflow (RBAC_info.md).

## The New Approach: Dynamic Form Generation

Instead of a single, hard-coded data extraction form, the system will provide a form builder. This allows project owners to define a custom form for each systematic review project, tailored to its specific protocol.

When a user is ready to extract data for a study, the application will dynamically generate the web form based on the definition stored in the database for that project.

## 1. Revised Database Models (`models.py`)

To support dynamic forms, we will use the following database schema:

*   **`Project`** and **`Study`**: These existing models will be used. The `Project` will serve as the anchor for its custom form definition.

*   **`CustomFormField` (New Model)**: This model will define each individual field (or "question") in a project's data extraction form.
    *   `project_id`: A foreign key linking the field to its `Project`.
    *   `section`: A string to group related fields together in the UI (e.g., "Study Characteristics", "Participants", "Outcomes").
    *   `label`: The human-readable name for the field that will be displayed in the form (e.g., "Population description").
    *   `field_type`: The type of input, which determines how it is rendered in the UI (e.g., `text`, `textarea`, `integer`, or more complex custom types like `dichotomous_outcome`).
    *   `required`: A boolean to indicate if the field is mandatory.

*   **`StudyDataValue` (New Model)**: This model will store the actual data entered by a user for a specific study. It functions as a key-value store.
    *   `study_id`: A foreign key linking the data to the `Study`.
    *   `form_field_id`: A foreign key linking the data to the `CustomFormField` that defines it.
    *   `value`: The data entered by the user. For simple types, this will be text. For complex types (like a dichotomous outcome), this could be stored as a JSON object.

## 2. New User Workflow

This new model structure enables the following user workflow:

### Step 1: Project Setup (Form Creation)

1.  A user creates a new `Project`.
2.  The system prompts them to choose the study design for their review (e.g., "Randomized Controlled Trial").
3.  Based on this choice, the system pre-populates the project's form with a suggested set of fields (stored as `CustomFormField` records) based on a standard template like the Cochrane form.
4.  The user can then **add, edit, or remove fields** to customize the form to the exact needs of their project's protocol. For instance, they can add a new `dichotomous_outcome` field and label it "Mortality at 30 days".

### Step 2: Data Extraction (Form Usage)

1.  When a user adds a `Study` to the project and begins data extraction, the application dynamically generates the form.
2.  The system reads all the `CustomFormField` entries for that project and renders the appropriate HTML input for each one.
3.  When the user submits the form, the application saves the data by creating a `StudyDataValue` record for each field that was filled out.

## 3. Form Builder User Experience (UX)

To facilitate the creation of custom forms, we will provide a simple, guided user experience.

### Step A: Entry Point

1.  After creating a new `Project`, the user is redirected to a **"Project Setup / Form Builder"** page.
2.  This page can also be accessed later from the project's main detail page.

### Step B: Choosing a Base Template

The first step on the setup page is to choose a starting template:

> **Select a template to start with:**
>
> *   `[ o ]` **Randomized Controlled Trial (RCT):** A comprehensive template based on the Cochrane handbook.
> *   `[   ]` **Start from scratch:** Build your form with no pre-defined fields.
>
> `[ Create Form ]`

Upon selection, the system generates the corresponding `CustomFormField` records for the project.

### Step C: The Form Customization Interface

After selecting a template, the user is presented with the main form builder interface. This UI will display all the fields for the project's form, grouped by section, in an interactive way.

A wireframe for this interface:

```
------------------------------------------------------------------
Project: [Your Project Name] > Data Extraction Form Builder
------------------------------------------------------------------

                                                  [ Save and Finish ]

---
Section: Study Characteristics                  [ Edit ] [ Delete ]
------------------------------------------------------------------
  - Label: Aim of study
    Type:  Text
                                                  [ Edit ] [ Delete ]
  - Label: Study design
    Type:  Text
                                                  [ Edit ] [ Delete ]

  [ + Add field to this section ]

---
Section: Outcomes                                 [ Edit ] [ Delete ]
------------------------------------------------------------------
  - Label: Mortality at 30 days
    Type:  Dichotomous Outcome
                                                  [ Edit ] [ Delete ]

  [ + Add field to this section ]

------------------------------------------------------------------
[ + Add New Section ]
------------------------------------------------------------------
```

**Key features of this interface:**

*   **Sections:** Fields are grouped into logical sections. Users can add, edit, and remove sections.
*   **Field Management:** Users have full control to `add`, `edit`, and `delete` fields within each section.
*   **Field Editor:** When adding or editing a field, a simple form or modal will appear to define its properties (e.g., `label`, `field_type`, `required`).
*   **Special Field Types:** The `field_type` dropdown will include simple types (`Text`, `Text Area`, `Integer`) as well as complex, pre-defined types like `Dichotomous Outcome`.

## 4. Developer Experience: Managing Base Templates

To make the base templates easy to manage and modify for developers, we will not hardcode them in the application logic. Instead, we will use external configuration files.

### YAML for Template Definitions

We will use YAML files to define the structure of each base template. This approach was chosen because YAML is highly human-readable, supports comments, and cleanly decouples configuration from code.

**Implementation Details:**

1.  **Directory:** A new directory will be created at `app/form_templates/`.
2.  **Template File:** For the RCT template, a file named `rct_template.yaml` will be placed in this directory.
3.  **Structure:** The YAML file will define the template's name, ID, and a list of sections, each containing a list of fields with their properties (`label`, `field_type`).

**Example `rct_template.yaml` snippet:**

```yaml
# Base template for Randomized Controlled Trials (RCTs)
template_name: "Randomized Controlled Trial (RCT)"
template_id: "rct_v1"

sections:
  - section_name: "Study Identification"
    fields:
      - label: "Study ID"
        field_type: "text"
      - label: "Reference citation"
        field_type: "textarea"
  
  # ... and so on for all other sections.
```

**Workflow Integration:**

The process described in "Step B: Choosing a Base Template" will be implemented by reading and parsing the appropriate YAML file from the `app/form_templates/` directory when a user makes their selection. This populates the `CustomFormField` table in the database.
