# Come cambiare modello Claude in Claude Code

---

## Durante una sessione attiva

Digita direttamente nella chat:

```
/model
```

Apparirà un selettore interattivo con i modelli disponibili. Seleziona quello desiderato e la sessione corrente userà il nuovo modello da quel momento in poi.

In alternativa, puoi specificarlo direttamente senza picker:

```
/model claude-opus-4-8
```

---

## Avviare una nuova sessione con un modello specifico

Dal terminale, passa il flag `--model` al comando `claude`:

```bash
claude --model claude-opus-4-8
```

```bash
claude --model claude-haiku-4-5-20251001
```

---

## Impostare un modello di default persistente

Per non dover specificare il modello ogni volta, usa `/config` dentro Claude Code:

```
/config
```

Cerca il campo `model` e imposta il valore desiderato. L'impostazione viene salvata e usata in tutte le sessioni future.

---

## Modelli disponibili

| Model ID | Caratteristiche |
|---|---|
| `claude-sonnet-4-6` | Bilanciato — default attuale |
| `claude-opus-4-8` | Più capace, più lento |
| `claude-haiku-4-5-20251001` | Più veloce e leggero |
| `claude-fable-5` | Modello più recente |

---

## Modalità Fast

Il comando `/fast` non cambia modello ma attiva una modalità di output più veloce su Opus. Si toglie con `/fast` di nuovo (toggle).

---

## Note

- Cambiare modello durante una sessione non cancella la cronologia della conversazione.
- Il modello attivo è sempre visibile nella barra di stato in basso nell'interfaccia Claude Code.
- In VS Code extension, il modello può anche essere impostato nelle impostazioni dell'estensione.
