# Spec — Homepage www.joliemachine.com

**Date :** 2026-04-18
**Instance Odoo :** `ocb` sur `http://127.0.0.1:8069` (future prod : www.joliemachine.com)
**Website Odoo :** `website` id=1 (« My Website », company « Jolie Machine »)
**Objectif :** refondre la homepage en vitrine des formations Odoo × Claude via `odoo-mcp-18` / `odoo-mcp-19`, proposant un parcours par audience et valorisant les routines + skills métiers.

---

## 1. Positionnement

Joliemachine vend des **formations** qui permettent aux entreprises utilisant Odoo (17, 18 ou 19) de :

1. **Piloter Odoo par conversation** avec Claude, via le serveur MCP `odoo-mcp-adv` (outils `execute_method` et `batch_execute`).
2. **Connecter Odoo à n'importe quel service** (API ou webhook) grâce à des **routines** — automatisations conversationnelles réutilisables.
3. **Disposer d'un assistant proactif** qui surveille l'état des modules activés (CRM, Sales, Stock, Invoicing, HR, Project, etc.) et propose les actions utiles au bon moment.
4. **Préserver l'identité de l'entreprise** : l'assistant apprend les **skills métiers** propres à chaque utilisateur Odoo — vocabulaire, règles de décision, tours de main — sans imposer de standard externe.

**Claim principal :** *« Votre ERP Odoo, piloté par conversation. »*
**Sous-claim :** Formations pour dirigeants, DSI, responsables métier et utilisateurs quotidiens.

### Audiences (hiérarchie 4 niveaux)

| Niveau | Rôle | Durée | Spécificité |
|---|---|---|---|
| N4 | Dirigeants & décideurs | 2 × ½ j | Supervision globale — vue transverse sur les niveaux inférieurs |
| N3 | DSI & responsables IT | 3 j | Intégration, gouvernance, sécurité — vue sur métiers + utilisateurs |
| N2 | Responsables métier (CRM, Sales, Ops, Compta…) | 2 j | Pilotage d'équipes, routines de module, vue utilisateur |
| N1 | Utilisateurs quotidiens | 1 j | `assistant-daily` — routines de check matinal, tâches suggérées |

Les rôles à responsabilités (N2 → N4) héritent de la **visibilité** sur les niveaux inférieurs pour la supervision. Cette hiérarchie est un élément différenciateur majeur repris dans le catalogue et dans la section Skills métiers.

---

## 2. Stratégie linguistique

- **Bilingue FR + EN** (switcher dans le header).
- Langue par défaut du website : **FR** (à changer depuis EN sur website id=1).
- `fr_FR` (id=30) déjà actif sur l'instance, à ajouter à `website.language_ids`.
- Le contenu est rédigé **en FR natif** puis traduit EN via Odoo (model.translation) après validation.
- Domaine cible : **www.joliemachine.com** (à configurer sur `website.domain`).

---

## 3. Direction visuelle

**Hybride A + C** validé par le commanditaire :

- **Palette primaire** : navy `#0b1d3a` → `#1a3a6c` (corporate, trust-first, hérité de A).
- **Accent chaud** : orange `#ea580c` / terracotta `#c2410c` + crème `#fef3e2` → `#fde2c4` (pédagogique, inviting, hérité de C).
- **Typographie** : `-apple-system` / `Inter` pour le titrage, tracking serré (`letter-spacing: -.5px` sur h1/h2).
- **Tonalité rédactionnelle** : affirmative, concrète, sans jargon IA. Ex. *« Arrêtez de cliquer dans 20 menus »* plutôt que *« Maximisez la productivité grâce à l'IA »*.

**Références** : Microsoft Copilot, Anthropic (pour la sobriété corporate) ; Notion, Loom, Maven (pour le ton pédagogique).

---

## 4. Structure de la page — 11 sections

### 4.1 Header / navigation

- Logo joliemachine (dégradé navy → orange, placeholder 28×28)
- Liens : **Formations** (`/formations`) · **Routines** (`/routines`) · **Tarifs** (`/tarifs`) · **Démo** (`/demo`) · **Contact** (`/contactus`, déjà existant)
- Switcher langue **FR · EN** aligné à droite — utiliser le snippet natif Odoo `website.language_selector` (dropdown basé sur `website.language_ids`)

### 4.2 Hero (fond navy)

- Eyebrow : `JOLIEMACHINE · FORMATIONS ODOO × CLAUDE`
- Titre H1 : *« Votre ERP Odoo, piloté par **conversation**. »* (mot "conversation" en orange)
- Sous-titre : *« Formations pour dirigeants, DSI, responsables métier et utilisateurs quotidiens. Parlez à Odoo en langage naturel via Claude — et connectez-le à tout service API ou webhook grâce aux routines. »*
- CTA primaire : **Réserver une formation →** (orange solide) — `href="/formations"` (404 accepté phase 1)
- CTA secondaire : **Voir la démo (15 min)** (outlined blanc) — `href="/demo"` (404 accepté phase 1)

### 4.3 Proof line

Bandeau discret en bas de hero : `● COMPATIBLE ODOO 17 · 18 · 19` · `● MCP 2025` · `● CLAUDE SONNET & OPUS`.

### 4.4 Value trio (3 colonnes)

Chaque colonne : pictogramme (fond crème), titre court, 2 phrases.

1. **Parlez à Odoo** — *Claude lit, écrit, analyse vos données Odoo. Fini les clics dans 20 menus — une phrase suffit.*
2. **Routines universelles** — *Connectez Odoo à n'importe quel service API ou webhook. Automatisez ce qui rentre, ce qui sort, ce qui change.*
3. **Assistant proactif** — *Votre assistant observe l'état du CRM, des ventes, des envois, **et plus largement de tous les modules Odoo que vous utilisez**. Il vous propose les actions utiles, au bon moment.*

### 4.5 Catalogue des 4 formations

Fond ivoire `#fafaf9`. Titre central :

- Eyebrow : `● CATALOGUE DE FORMATIONS`
- H2 : *« Un parcours adapté à chaque rôle »*
- Sous-titre : *« Du dirigeant à l'utilisateur quotidien — les décideurs voient aussi les processus des niveaux inférieurs pour la supervision. »*

Puis grille 2×2 de cards (bordure grise sauf la carte N1 **mise en avant** bordure orange 2px) :

| Eyebrow | Titre | Badge durée | Résumé |
|---|---|---|---|
| `NIVEAU 4 · SUPERVISION GLOBALE` | Dirigeants & décideurs | `2 × ½ j` | Vision stratégique + supervision DSI/métier/terrain. Tableaux de bord conversationnels, alerting, scénarios "what-if". |
| `NIVEAU 3 · INTÉGRATION` | DSI & responsables IT | `3 jours` | Déploiement MCP, routines, gouvernance, sécurité, monitoring. Vue sur tous les niveaux pour supervision. |
| `NIVEAU 2 · PILOTAGE MÉTIER` | Responsables (CRM, Sales, Ops…) | `2 jours` | Construction de routines sur leur module, pilotage des équipes, indicateurs. Vue sur les utilisateurs pour accompagnement. |
| `NIVEAU 1 · USAGE QUOTIDIEN ★` | Utilisateurs · `assistant-daily` | `1 journée` | L'assistant-daily : routines de check matinal, tâches suggérées, relances. Odoo devient un collègue qui connaît le dossier. |

Lien de chaque card : `En savoir plus →` (deep-link vers `/formations/{slug}` — les 4 pages de détail sont hors scope de ce spec, créées en phase 2).

### 4.6 Routines spotlight (fond navy)

Layout 2 colonnes (1:1) :

- **Gauche :** eyebrow `● ROUTINE EN ACTION`, H2 *« Un lead rentre sur le CRM. Votre routine fait le reste. »*, paragraphe description, bouton outlined `Voir toutes les routines →`.
- **Droite :** bloc "terminal" stylé (fond semi-transparent, police mono) montrant une routine qui s'exécute :
  ```
  ┌─ NOUVEAU LEAD · CRM
  │ ACME Corp · contact@acme.fr
  ├─ Enrichissement (Clearbit API)
  │ 250 emp · SaaS B2B · Paris
  ├─ Scoring → 82/100
  ├─ Assigné → Sophie (EMEA)
  ├─ Email bienvenue (FR) ✓
  └─ Tâche : rappel à J+2
  → 4.2 sec · 0 clic
  ```

### 4.7 Skills métiers (nouvelle section — dégradé blanc → ivoire)

- Eyebrow : `● SKILLS MÉTIERS · APPRENTISSAGE CONTINU`
- H2 : *« Votre entreprise garde son identité. L'assistant apprend la vôtre. »*
- Sous-titre : *« Pas de standardisation imposée. Chaque utilisateur Odoo transmet ses compétences métier à l'assistant — vocabulaire, règles de décision, tours de main. Votre savoir-faire reste chez vous, et il devient actionnable. »*

**Grille 2×2 de personas + skills appris :**

| Persona | Modules | Skills appris |
|---|---|---|
| **Sophie · Commerciale EMEA** | CRM · Sales | Scripts de qualif maison (BANT revisité) · Grille de remises par segment & volume · Séquence de relances "Sophie-style" · Règles d'escalade sur gros comptes |
| **Marc · ADV / SAV** | Helpdesk · Stock · Invoicing | Clients prioritaires & délais promis · Arbre de diagnostic SAV (5 niveaux) · Règles de remplacement vs réparation · Ton de réponse client (formel/familier) |
| **Léa · Comptabilité** | Accounting · Analytic | Plan analytique maison (projets × canaux) · Fournisseurs récurrents & codes courts · Règles de lettrage automatique · Tolérances de rapprochement bancaire |
| **Julien · Directeur général** | Vue globale · Supervision | Seuils d'alerte cash, marge, run-rate · Rituels hebdo (COMEX, revue pipeline) · **Hérite des skills de Sophie, Marc, Léa** · Questions types du board & formats |

**Bandeau principe final** (fond navy, coin arrondi) :

> 🔒 **Le savoir-faire reste chez vous**
> *Les skills sont versionnés, auditables, exportables. Un collaborateur part : son savoir-faire ne disparaît pas. Un nouveau arrive : il démarre avec les skills de son poste. Aucune standardisation cloud, aucune fuite vers un modèle tiers.*

### 4.8 Social proof (fond blanc)

Zone centrée, placeholder clair :

- Eyebrow : `● ILS ONT FRANCHI LE PAS`
- Citation placeholder : *« Nos commerciaux ne cliquent plus dans Odoo. Ils demandent, ça se fait. On a gagné 1h par jour et par personne. »*
- Attribution : *« Placeholder témoignage · À remplir avec vrais clients »* (tag visible en orange clair pour que l'équipe sache que c'est à remplacer)

### 4.9 Final CTA band (fond crème → orange pastel)

- H2 : *« Prêt à transformer votre Odoo ? »*
- Sous-titre : *« Démo de 15 minutes · Devis formation sous 48 h »*
- Double CTA : **Réserver une formation** (navy solide) + **Planifier une démo** (outlined navy)

### 4.10 Footer (fond navy, compact)

- `joliemachine · Formations Odoo × Claude · FR · EN — © 2026`
- Phase 2 : liens mentions légales, RGPD, contact support.

---

## 5. Implémentation Odoo

### 5.1 Modèles utilisés

- **`website.page`** — remplacer le contenu de la page id=4 (url `/`, `is_homepage=True`) par l'arch QWeb décrite ci-dessous.
- **`website.menu`** — ajouter les entrées Formations, Routines, Tarifs, Démo sous `parent_id=4` (Top Menu for Website 1). Conserver les menus Home (id=5), Shop (id=7), Contact us (id=6) existants. Séquences : Home=10 (conservé), Formations=20, Routines=30, Tarifs=40, Démo=50, Contact us=60 (conservé), Shop=déplacé à 70 ou caché si non prioritaire.
- **`website`** — id=1 :
  - `domain` → `www.joliemachine.com`
  - `language_ids` → ajouter `fr_FR` (id=30)
  - `default_lang_id` → `fr_FR`
- **`ir.ui.view`** — la vue `arch` de la homepage contient le markup complet.

### 5.2 Structure QWeb

Chaque section = un `<section>` HTML avec classes Bootstrap (`container`, `row`, `col-*`) et classes Odoo snippet (`s_text_block`, `s_cover`, `s_features_grid`, `s_call_to_action`) pour rester compatible avec l'éditeur Website d'Odoo et ne pas casser l'édition WYSIWYG.

Convention :
- Classes Bootstrap 5 (Odoo 17+) : `row`, `col-md-4`, `g-4`…
- Classes de couleur Odoo : `bg-o-color-1` (primary = navy), `bg-o-color-2` (accent), `text-white`.
- Overrides inline limités à ce que les classes natives ne permettent pas (gradients hero, mockup terminal).

### 5.3 Assets

- **Logo** : à produire (placeholder = dégradé navy → orange 28×28). Dimensions finales 96×96 px (retina), livré en SVG si possible, sinon PNG 2×.
- **Pictogrammes value trio** : emoji pour v1 (💬 ⚡ 🎯), remplaçables par SVG en phase 2.
- **Images personas Skills métiers** : emoji pour v1 (👩‍💼 👨‍🔧 👩‍💻 👨‍💼), remplaçables par photos stock ou illustrations.

### 5.4 SEO

- `website_meta_title` : *« joliemachine — Formations Odoo × Claude | Pilotez votre ERP par conversation »*
- `website_meta_description` : *« Formations Odoo pour dirigeants, DSI, responsables et utilisateurs. Parlez à Odoo avec Claude, connectez vos modules via routines, préservez votre savoir-faire. »*
- `website_meta_keywords` : odoo, claude, mcp, formation, routines, assistant, erp conversationnel

### 5.5 Publication

- `is_published = True` sur `website.page` id=4.
- Test : charger `/` (FR) et `/en/` une fois traduit.

### 5.6 Traduction EN

Hors scope de l'implémentation initiale. Après validation de la version FR :
1. Activer le mode dev, passer en langue EN.
2. Éditer chaque bloc depuis le front-end : Odoo crée automatiquement les `ir.translation` / `model.translation` correspondants.
3. Vérifier le switcher, vérifier le routing `/en/`.

---

## 6. Hors scope

Explicitement **pas** couvert par ce spec (phases suivantes ou à clarifier) :

- Pages de détail des 4 formations (`/formations/{slug}`) — à spécifier une fois la homepage validée.
- Pages `/routines` (catalogue détaillé), `/tarifs` (grille tarifaire), `/demo` (formulaire calendly ou contact).
- Système de réservation (formulaire → CRM lead, intégration calendrier).
- Intégration paiement formation (Stripe via `website_sale` ?).
- Contenu pages mentions légales / RGPD.
- Vrais témoignages clients (placeholder pour l'instant).
- Images personas et pictogrammes finaux (emoji pour v1).
- Traduction EN (activée après validation FR).
- Logo vectoriel définitif.
- Configuration DNS `www.joliemachine.com` → instance (pas de notre ressort ici).
- Pixel analytics / cookie banner / consent.

---

## 7. Hypothèses

- Le website éditeur d'Odoo (`website`) accepte un `arch` QWeb riche sans perdre l'éditabilité WYSIWYG tant qu'on respecte les classes de snippets standard.
- Les modifications de `website.language_ids` et `website.domain` sont autorisées par le user lors de l'implémentation (actuellement bloquées par le permission hook — à débloquer au moment de l'exécution).
- La company `Jolie Machine` (id=1) reste la seule, pas de multi-company.
- Pas de besoin de responsive spécifique au-delà de Bootstrap 5 mobile-first (la grille 2×2 devient 1×4 sur mobile).

---

## 8. Critères d'acceptation

La homepage est considérée livrée quand :

1. `/` retourne la page sur `http://127.0.0.1:8069` avec les 11 sections dans l'ordre.
2. Le switcher FR/EN est visible dans le header (même si EN vide pour l'instant).
3. Les CTAs primaire et secondaire du hero pointent vers des URLs valides (`/formations`, `/demo` — 404 acceptables en phase 1, elles seront créées en phase 2).
4. Les menus Formations · Routines · Tarifs · Démo · Contact sont visibles dans la nav.
5. Aucune régression sur les autres pages (`/shop`, `/contactus`).
6. Page éditable depuis l'éditeur Website sans casser le markup.
7. SEO meta renseignés.
8. `is_published = True`.

---

## 9. Risques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| L'éditeur Website d'Odoo casse le markup custom lors d'une édition | Moyen | Utiliser classes snippets standard (`s_text_block`, `s_cover`, `s_call_to_action`) quand possible ; documenter les blocs custom. |
| La section Skills métiers (personas fictives) peut créer de la confusion juridique | Faible | Marquer "exemples" clairement dans le sous-titre + disclaimer footer phase 2. |
| Bilingue FR/EN : coût de maintenance double | Moyen | Phase 1 : FR uniquement, EN activé plus tard. Accepté explicitement. |
| Compatibilité inter-versions Odoo (17/18/19) du markup | Faible | Bootstrap 5 + snippets standards = compatible Odoo 16+. À tester sur chacune des 3 versions avant release de la page de vente. |
| Lien `/formations/{slug}` 404 en phase 1 | Faible | Acceptable. Tracker les 404 pour prioriser les pages de détail. |

---

## 10. Références

- Mockup v1 : `.superpowers/brainstorm/46953-1776602017/content/homepage-mockup.html`
- Mockup v2 (ajout Skills métiers) : `.superpowers/brainstorm/46953-1776602017/content/homepage-mockup-v2.html`
- Projet parent MCP : `/Users/alanogic/ddev/mcp-odoo-adv`
- Odoo API docs : https://www.odoo.com/documentation/18.0/developer/reference/frontend/qweb.html
- Snippets Odoo : `addons/website/views/snippets/*.xml`
