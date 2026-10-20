# Support de soutenance — Groupe 1 : bibliothèque

## Plan (15 minutes)

1. **Contexte et question (2 min)** — Décrire la table d’événements d’emprunt et les
   référentiels. Question : quels sites et familles concentrent l’activité, les retards et
   les pertes, et quelle est leur évolution mensuelle ?
2. **Diagnostic (3 min)** — Présenter les 20 563 événements, les 412 dates manquantes,
   les 1 841 durées absentes, les 180 occurrences supplémentaires d’identifiants réutilisés,
   les variantes de statut et les taux de clés orphelines recalculés par le notebook.
3. **Traitements (5 min)** — Montrer le parsing explicite des dates, la normalisation des
   textes, la distinction entre doublon exact et id réutilisé, le maintien des durées
   manquantes et les jointures gauches contrôlées.
4. **PySpark (2 min)** — Montrer `src/library_pipeline.py`, le broadcast des référentiels
   et les mesures observées dans le notebook. Préciser que le RSS Python ne mesure pas la
   mémoire complète de la JVM Spark.
5. **Résultats et limites (3 min)** — Présenter emprunts, retards et pertes par région et
   famille, l’évolution mensuelle et les limites du jeu synthétique.

## Questions probables

- **Pourquoi conserver les identifiants d’emprunt répétés ?** Ils peuvent correspondre à
  des états ou corrections différents. Seules les lignes strictement identiques sont
  supprimées avant une vérification métier des ids réutilisés.
- **Pourquoi conserver les durées absentes ?** Aucune autre colonne ne permet de les
  reconstruire. Elles restent dans le volume d’activité, mais ne contribuent pas à la
  durée moyenne.
- **Comment définir un retard ?** Le statut est normalisé, puis `en_retard` est compté.
  Le jeu ne fournit pas de date d’échéance fiable permettant de recalculer le retard.
- **Que signifie la valeur perdue ?** C’est la valeur de l’ouvrage déclarée dans l’événement
  au statut `perdu`, pas une perte financière auditée.
- **Pourquoi les jointures sont gauches ?** Pour conserver les événements et mesurer les
  clés absentes des référentiels plutôt que les masquer.
- **Pourquoi Spark ?** Le TP mesure son coût fixe sur les données locales. L’intérêt attendu
  est la capacité à traiter des volumes distribués, pas une vitesse supérieure garantie ici.

## À compléter avant le dépôt

- noms des membres et date de soutenance ;
- résultats chiffrés et graphique produits par le notebook ;
- validation métier du traitement des identifiants d’emprunt réutilisés.
