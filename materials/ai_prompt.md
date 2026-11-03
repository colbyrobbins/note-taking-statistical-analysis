# AI summaries (condition: "AI summary")

Each summary was generated **once**, in a separate new ChatGPT chat per part, and is shown
**unchanged** to every participant in the AI condition. Summaries were requested as bullet points
to mirror the format of typical handwritten notes.

- **Model:** GPT-6 in ChatGPT (as shown in the ChatGPT interface)
- **Date generated:** 2026-10-27
- **Source transcript:** Spanish-language YouTube transcript (translation by Lidia Camara de la Fuente,
  reviewed by Ciro Gomez) of "Meet the tardigrade, the toughest animal on Earth"
  (Thomas Boothby, TED-Ed), https://www.youtube.com/watch?v=IxndOd3kmSs. The prompt asks for an
  English summary; participants watch the original English video.
  - Part 1: 0:00–2:17 ("Without water…" to "…the vacuum of outer space")
  - Part 2: 2:17–3:55 ("This has led to the mistaken speculation…" to the end)

## Prompt (identical for both parts)

```
Summarize the following excerpt from an educational video transcript as study notes for a student
who will be quizzed on it. Write 6–8 concise bullet points (about 100 words in total) in plain
English. Do not add any information that is not in the transcript.

[transcript of Part 1 / Part 2, timestamps and captions credits removed]
```

## Output: Part 1 (exactly as generated)

* Humans can survive only about 100 hours without water, but tardigrades can survive decades without it.
* Tardigrades, also called water bears, are about 1 millimeter long and have eight legs.
* Water is essential for metabolism, which involves biochemical reactions inside cells.
* Tardigrades survive dehydration through anhydrobiosis, meaning “life without water.”
* During dehydration, they enter a tun state, curling into a ball and folding their head and legs inward.
* Special molecules form a protective matrix around DNA, proteins, and cell membranes, preventing damage.
* When water returns, the matrix dissolves, leaving the cells functional again.
* Tardigrades also tolerate freezing, extreme heat, high radiation, and the vacuum of space.

## Output: Part 2 (exactly as generated)

* Earthly origin: Tardigrades are not aliens. Scientific evidence shows they evolved on Earth.
* Species: More than 1,100 species are known, and many more may remain undiscovered.
* Worldwide distribution: Tardigrades live on every continent, including Antarctica.
* Habitats: They survive in deserts, polar ice, oceans, freshwater, rainforests, and high mountains.
* Finding them: They can be found in moss and lichens in parks, yards, and forests using a microscope.
* Survival research: Scientists study whether their protective tun state helps them survive other stressful conditions.
* Practical applications: Research may help preserve vaccines and develop stress-resistant crops.
* Space research: Their survival in space's vacuum may reveal life's limits and ways to protect astronauts.

## Coverage check (does the summary contain each quiz answer?)

Assessed before data collection (quiz version 1.1.0); stored per item as `summary_coverage` in
`materials/study_materials.json` and carried into `answer_key.csv`.

| Item | Part 1 | Part 2 |
|---|---|---|
| q01 | full | full |
| q02 | partial ("head and legs", not "all eight legs") | full |
| q03 | full | full |
| q04 | partial (matrix mentioned, not that it replaces water) | full |
| q05 | partial ("preventing damage", not unfold/break/fuse) | partial ("preserve vaccines", not stabilizing molecules) |
| q06 | none (other organisms not mentioned) | none (harsher-planets question not mentioned) |

**Total: 6 of 12 full, 4 partial, 2 none.** The summaries were not regenerated or edited:
omissions are part of what relying on an AI summary means in practice. A robustness analysis
repeats the primary comparison on the 6 fully covered items only.
