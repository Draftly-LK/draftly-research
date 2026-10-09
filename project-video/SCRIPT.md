# Draftly demo video: narration sheet

Generated from `src/script.ts`. Edit the lines there, then run
`node scripts/export-script.cjs` to refresh this sheet.

Read at a calm pace (about 140 words a minute). Record each section as its
own audio file, named as shown, into `public/audio/`, then list it in
`src/media.ts`.

## 0:00–1:05 · 1 · The problem

- On-screen text: “A property transfer starts with documents.”
- Length: 65 s (122 words)
- Audio file: `public/audio/problem.mp3`

> A client arrives with a simple request: help me transfer this property.
>
> Behind that request is a careful legal workflow.
>
> The notary must read the documents, identify the parties, compare the property details, examine the supporting records, find the relevant law and prepare the instrument.
>
> The information can be scattered across scanned pages, handwritten entries and documents in different languages.
>
> Reading each page is only part of the task. The lawyer also has to establish how the documents relate to one another, which details can be relied on, and what still needs clarification.
>
> Legal research adds another layer: finding a relevant provision, checking its context and connecting it to the evidence in the matter.
>
> That connection is the problem our project addresses.

## 1:05–1:35 · 2 · Why we built Draftly

- On-screen text: “Shaped by practitioners and research guidance.”
- Length: 30 s (67 words)
- Audio file: `public/audio/why.mp3`

> We began by speaking with four lawyers about their notarial and conveyancing work.
>
> Those discussions shaped two priorities: managing matter evidence and retrieving supporting law.
>
> One lawyer helped us develop the workflow, while an expert in legal information retrieval and natural language processing supported the research component.
>
> That guidance shaped Draftly: a workspace for Sri Lankan notarial and conveyancing practice, with the lawyer making the decisions throughout.

## 1:35–2:15 · 3 · The document bundle

- On-screen text: “One bundle. Several questions.”
- Length: 40 s (73 words)
- Audio file: `public/audio/bundle.mp3`

> We're following a synthetic client bundle, invented for this demonstration.
>
> It includes identity and property records, a transfer instrument, a company resolution and a payment record.
>
> The extraction workflow supports four document types. Other supporting records need manual review. A company resolution, for example, must be read to establish what it authorizes.
>
> Before using any particulars, the lawyer establishes the parties, property and intended transfer, and separates the supporting records from the background.

## 2:15–2:45 · 4 · Manual workflow and Draftly

- On-screen text: “Keep the detail connected to its evidence.”
- Length: 30 s (65 words)
- Audio file: `public/audio/compare.mp3`

> In a manual workflow, the lawyer moves between pages, notes, legal sources and the draft, repeatedly checking the same details.
>
> With Draftly, those documents belong to a matter. Proposed information can be reviewed beside its source, and confirmed particulars can support the working instrument.
>
> The lawyer still decides what the evidence means. Draftly helps organize the information and preserve the connection behind each reviewed value.

## 2:45–3:25 · 5 · Open and scope the matter

- On-screen text: “Start with the right transaction.”
- Length: 40 s (80 words)
- Audio file: `public/audio/matter.mp3`

> We begin by defining the matter.
>
> The lawyer sets the registration system and the intended workflow: here, a transfer by sale under the Registration of Title Act.
>
> A few routing questions follow: the scope of the transfer, the kind of parcel, the parties, and whether a dispute is known.
>
> Draftly uses these answers to organize the requirements into a checklist.
>
> We then choose the document bundle from the computer and attach it, bringing the evidence into one workspace for review.

## 3:25–4:35 · 6 · Read the documents and verify a fact

- On-screen text: “Proposed information becomes a fact through review.”
- Length: 70 s (122 words)
- Audio file: `public/audio/verify.mp3`

> The original documents remain the evidence.
>
> Processing proposes document types and the particulars it can read. This recording uses prepared extraction results to demonstrate the review workflow.
>
> The lawyer confirms each document's type, then checks each proposed value against its source page.
>
> Here, we open the title certificate and inspect a proposed property detail beside the page it came from.
>
> The lawyer corrects the reading if necessary, and approves it, one value at a time or all together.
>
> Once every document is reviewed, the matter holds forty-six verified facts, each one a decision the lawyer has made.
>
> Now the reviewed value has a source the lawyer can return to. If that fact changes, affected checks and draft fields need a fresh review.

## 4:35–5:30 · 7 · Investigate a difference

- On-screen text: “A difference is a question to investigate.”
- Length: 55 s (105 words)
- Audio file: `public/audio/difference.mp3`

> Review also means checking how the records relate to one another.
>
> A bundle can contain different property references. We need to establish what each reference describes.
>
> The records may concern an earlier transfer, related land or a different part of the transaction history.
>
> Draftly's implemented checks compare the verified facts with the rules for this transaction. Here they raised twelve warnings.
>
> The lawyer opens each issue and records a decision. If the relationship is still unclear, the question stays open until the evidence is there to resolve it.
>
> The useful outcome is a matter that shows what has been established and what still needs attention.

## 5:30–6:25 · 8 · Prepare the working instrument

- On-screen text: “From reviewed fact to working instrument.”
- Length: 55 s (98 words)
- Audio file: `public/audio/instrument.mp3`

> Once the required particulars have been reviewed, we move to the working instrument.
>
> Draftly opens the prescribed Form 8 and fills the supported fields from the confirmed facts.
>
> Here is a detail we reviewed earlier, now in its field. The lawyer can follow it back to its evidence. Missing particulars stay visible for resolution.
>
> The prescribed wording is locked. Only the blanks can change, and each populated field still needs the lawyer's confirmation.
>
> A populated form is still a working draft. The lawyer must examine its content, source text and completeness before deciding how it can be used.

## 6:25–7:05 · 9 · Review status and the matter record

- On-screen text: “See what is complete. See what remains.”
- Length: 40 s (79 words)
- Audio file: `public/audio/status.mp3`

> Preflight shows the form's review state. Review-ready and approval-ready pass. Registration-ready does not, because no template has been validated yet.
>
> For this demonstration, two matter-wide approval rules that remain open policy decisions are relaxed, and the lawyer approves the working form after reading the declaration.
>
> The matter record preserves the decisions made along the way. An internal export manifest records the form's state.
>
> Registration events record actions reported by the lawyer. Filing remains with the practitioner and the registry.

## 7:05–9:15 · 10 · Legal research and retrieval

- On-screen text: “Find the provisions behind the question.”
- Length: 130 s (196 words)
- Audio file: `public/audio/research.mp3`

> So far, we have examined what the documents say. The next question is what the law requires.
>
> Here, we open the dedicated Research workspace and select the source scope: all sources, statutes and amendments, or case law.
>
> The catalogue lists fifty-seven statutes and eighteen amendments, with a separate case-law tab.
>
> The retrieval challenge is finding the provisions a scenario needs. A transfer may raise several legal questions, with related requirements and amendments to examine.
>
> Our legal information retrieval research studies how to find those provisions and make the supporting material available for inspection.
>
> Here, we open a citation and read the passage behind the answer. Draftly's research workflow retains claims supported by the returned passages. When the available sources cannot support an answer, the gap stays visible.
>
> The lawyer still reads the provision, checks its context and decides whether it applies.
>
> Case-law results are research leads. The lawyer assesses the judgment's relevance and authority before relying on it.
>
> For evaluation, a reviewer compares retrieved passages with the provisions required by a scenario. That makes missed authorities visible as well as useful matches.
>
> The goal is research the lawyer can examine, alongside evidence the lawyer can trace.

## 9:15–10:00 · 11 · Return to the client and close

- On-screen text: “Follow the evidence. Keep the lawyer in control.”
- Length: 45 s (87 words)
- Audio file: `public/audio/closing.mp3`

> At the start, the client brought a bundle of documents.
>
> Now the lawyer has a structured matter. Reviewed particulars have a source, their evidence can be reopened, and unresolved questions remain visible. The required facts support an optional working instrument.
>
> The legal sources remain open to inspection. The decisions remain with the lawyer.
>
> That is the purpose of Draftly: support the careful work behind a property transfer, through a focused workflow for Sri Lankan notarial and conveyancing practice.
>
> Draftly. Follow the evidence. Keep the lawyer in control.

Total: 10:00
