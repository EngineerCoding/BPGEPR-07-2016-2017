DROP TABLE IF EXISTS Gen_07 CASCADE;
CREATE TABLE Gen_07 (
  gen_id NUMERIC(9, 0) PRIMARY KEY,
  gen_naam TEXT,
  accession_code VARCHAR(20),
  gen_sequentie TEXT
);

DROP TABLE IF EXISTS Exon_07 CASCADE;
CREATE TABLE Exon_07 (
  exon_id NUMERIC(9, 0) PRIMARY KEY,
  gen_id NUMERIC(9, 0),
  start_positie INTEGER,
  eind_positie INTEGER,


  FOREIGN KEY (gen_id) REFERENCES Gen_07(gen_id)
);

DROP TABLE IF EXISTS Eiwit_07 CASCADE;
CREATE TABLE Eiwit_07 (
  eiwit_id NUMERIC(9, 0) PRIMARY KEY,
  gen_id NUMERIC(9, 0),
  eiwit_naam TEXT,
  eiwit_sequentie TEXT,

  FOREIGN KEY (gen_id) REFERENCES Gen_07(gen_id)
);

DROP TABLE IF EXISTS Reactie_07 CASCADE;
CREATE TABLE Reactie_07 (
 	reactie_id VARCHAR(6) PRIMARY KEY,
  reactie TEXT,
  reactie_ec VARCHAR(15)
);

DROP TABLE IF EXISTS Pathway_07 CASCADE;
CREATE TABLE Pathway_07 (
 	pathway_id CHAR(8) PRIMARY KEY,
  pathway_naam TEXT,
  class TEXT,
  referentie_id INTEGER
);

DROP TABLE IF EXISTS EiwitPathway_07 CASCADE;
CREATE TABLE EiwitPathway_07 (
  eiwit_id NUMERIC(9, 0),
  pathway_id CHAR(8),

  FOREIGN KEY (eiwit_id) REFERENCES Eiwit_07(eiwit_id),
  FOREIGN KEY (pathway_id) REFERENCES Pathway_07(pathway_id)
);

DROP TABLE IF EXISTS EiwitReactie_07 CASCADE;
CREATE TABLE EiwitReactie_07 (
  eiwit_id NUMERIC(9, 0),
  reactie_id VARCHAR(6),

  FOREIGN KEY (eiwit_id) REFERENCES Eiwit_07(eiwit_id),
  FOREIGN KEY (reactie_id) REFERENCES Reactie_07(reactie_id)
);

DROP TABLE IF EXISTS Referentie_07 CASCADE;
CREATE TABLE Referentie_07 (
 	referentie_id INTEGER PRIMARY KEY,
  pathway_id CHAR (8),
  titel TEXT,
  journal TEXT,


	FOREIGN KEY (pathway_id) REFERENCES Pathway_07(pathway_id)
);

DROP TABLE IF EXISTS ReferentieAuteur_07 CASCADE;
CREATE TABLE ReferentieAuteur_07 (
 	auteur_id SERIAL,
  referentie_id INTEGER,


	FOREIGN KEY (auteur_id) REFERENCES Auteur_07(auteur_id),
  FOREIGN KEY (referentie_id) REFERENCES Referentie_07(referentie_id)
);

DROP TABLE IF EXISTS Auteur_07 CASCADE;
CREATE TABLE Auteur_07 (
  auteur_id   SERIAL PRIMARY KEY,
  auteur_naam TEXT
);

DROP TABLE IF EXISTS Domein_07 CASCADE;
CREATE TABLE Domein_07 (
 	domein_id SERIAL PRIMARY KEY,
  gem_domein_lengte NUMERIC(3,2),
  gem_alignment_coverage NUMERIC(3,2),
  gem_sequentie_coverage NUMERIC(3,2)
);

DROP TABLE IF EXISTS EiwitDomein_07 CASCADE;
CREATE TABLE EiwitDomein_07 (
 	eiwit_id NUMERIC(9,0),
  domein_id SERIAL,

	FOREIGN KEY (eiwit_id) REFERENCES Eiwit_07(eiwit_id),
  FOREIGN KEY (domein_id) REFERENCES Domein_07(domein_id)
);
