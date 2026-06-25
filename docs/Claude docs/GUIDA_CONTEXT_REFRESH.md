# Guida — Aggiornamento contesto e memorie
**Progetto:** OpenNetMap  
**Uso:** quando la context window si sta esaurendo, seguire questi passi prima di chiudere la sessione

---

## Quando farlo

- La sessione è lunga e Claude inizia a "dimenticare" dettagli delle prime conversazioni
- Si è completato uno sprint o un blocco di lavoro significativo
- Prima di chiudere una sessione con lavoro a metà
- Quando Claude avvisa che il contesto si sta comprimendo

---

## Checklist — cosa aggiornare

### 1. `docs/Claude docs/HANDOFF.md`
Il file più importante. Deve sempre riflettere lo stato **attuale**, non storico.

Aggiornare:
- [ ] **Branch di lavoro attivo** (quello su cui si sta lavorando ora)
- [ ] **Struttura branch Git** (quali branch esistono, quali PR sono aperte)
- [ ] **Sprint completati** — aggiungere il nuovo sprint con modifiche e risultati
- [ ] **Prossimi sprint** — rimuovere quello appena fatto, aggiornare il prossimo
- [ ] **Stato test e coverage** — ultima metrica registrata
- [ ] **Decisioni nuove** prese durante la sessione
- [ ] **Comandi utili** — aggiornare se il workflow è cambiato

### 2. `memory/roadmap-and-next-sprint.md`
Aggiornare con:
- [ ] Sprint appena completato (nome, branch, data)
- [ ] Prossimo sprint (nome e task principali)
- [ ] Branch attivo corrente

### 3. `memory/architectural-decisions.md`
Aggiornare con:
- [ ] Nuove decisioni architetturali prese nella sessione
- [ ] Decisioni revocate o modificate
- [ ] Nuove dipendenze aggiunte/rimosse con motivazione

### 4. `memory/sprint-workflow.md` e `memory/docs-organization.md`
Creare o aggiornare se durante la sessione l'utente ha:
- [ ] Corretto un approccio ("no, non così")
- [ ] Confermato un approccio non ovvio ("sì, esatto, continua così")
- [ ] Dato nuove istruzioni su come lavorare

### 5. `docs/Claude docs/TODO.md`
- [ ] Marcare completati i task dello sprint appena finito
- [ ] Aggiungere data esecuzione e branch al titolo dello sprint
- [ ] Aggiungere riepilogo risultati (black/ruff/mypy/pytest/coverage)

---

## Struttura delle memorie (riferimento rapido)

```
memory/
├── MEMORY.md                    ← indice (una riga per memoria)
├── user-profile.md              ← chi è l'utente, lingua, identità Git
├── sprint-workflow.md           ← come gestire gli sprint (feedback)
├── docs-organization.md         ← dove mettere i documenti Claude (feedback)
├── architectural-decisions.md   ← decisioni architetturali consolidate
└── roadmap-and-next-sprint.md   ← stato sprint e prossimo lavoro
```

> Nota: la directory delle memorie è gestita dal sistema di auto-memory di Claude Code
> (fuori dal repo). I nomi sopra sono quelli reali in uso; non usare nomi vecchi tipo
> `project_sprint_state.md` o `feedback_*.md`.

**Regola:** ogni file di memoria ha frontmatter YAML con `name`, `description`, `metadata.type`.  
Tipi disponibili: `user`, `feedback`, `project`, `reference`.

---

## Template per aggiungere una nuova memoria

```markdown
---
name: nome-kebab-case
description: Una riga che descrive il contenuto — usata per decidere la rilevanza
metadata:
  type: feedback  # oppure: user, project, reference
---

[Contenuto della memoria]

**Why:** [perché questa regola/decisione esiste]

**How to apply:** [quando e come applicarla]
```

Dopo aver creato il file, aggiungere una riga in `MEMORY.md`:
```markdown
- [Titolo](nome-file.md) — breve descrizione (max ~120 caratteri)
```

---

## Cosa NON mettere nelle memorie

- Codice sorgente o snippet (leggere direttamente i file)
- Cronologia git o chi ha cambiato cosa (usare `git log`)
- Stato temporaneo della sessione corrente
- Cose già documentate in `CLAUDE.md` o `README.md`
- Dettagli che si possono derivare dal codice

---

## Come scrivere HANDOFF.md in modo efficace

Il file deve rispondere a queste domande senza leggere altro:

1. **Dove siamo?** — branch attivo, PR aperte, ultimo commit
2. **Cosa è stato fatto?** — sprint completati con risultati numerici
3. **Cosa c'è da fare?** — prossimo sprint con task specifici e file da toccare
4. **Cosa NON fare?** — decisioni prese, cose da non rinegoziare
5. **Come ripartire?** — comandi copia-incolla pronti all'uso

Struttura consigliata:
```
# Handoff
[data]

## Stato branch Git
## Sprint completati (con risultati)
## Prossimo sprint (con task dettagliati)
## Decisioni consolidate
## File chiave
## Comandi per riprendere
## Note ambiente
```

---

## Sequenza operativa da seguire

```
1. Aggiorna docs/Claude docs/TODO.md (sprint completato)
2. Aggiorna docs/Claude docs/HANDOFF.md (stato completo)
3. Aggiorna memory/roadmap-and-next-sprint.md
4. Aggiorna memory/architectural-decisions.md (se ci sono nuove decisioni)
5. Crea/aggiorna memory/sprint-workflow.md o docs-organization.md (se nuovi feedback)
6. Aggiorna memory/MEMORY.md (se hai aggiunto nuovi file)
7. git add + git commit + git push (su branch attivo)
```

---

## Prompt per riprendere in una nuova sessione

Quando si inizia una nuova sessione, dire a Claude:

> "Riprendi il lavoro su OpenNetMap. Leggi `docs/Claude docs/HANDOFF.md` e le memorie del progetto per ripristinare il contesto, poi dimmi cosa hai capito prima di procedere."

Questo forza Claude a leggere il file e verificare la comprensione prima di agire.

---

## Segnali che il contesto sta per esaurirsi

- Claude ripete domande già poste in precedenza
- Claude "dimentica" decisioni prese (es. propone di rimuovere package che abbiamo deciso di tenere)
- Le risposte diventano più generiche e meno specifiche al progetto
- Compare l'avviso di compressione del contesto nella UI

**Quando noti uno di questi segnali:** interrompere e fare il refresh prima di continuare.
