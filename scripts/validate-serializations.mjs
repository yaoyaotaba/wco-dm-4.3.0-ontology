#!/usr/bin/env node
/**
 * Validate the three ontology serialisations and the SHACL samples.
 *
 * Install once:
 *   npm install n3 rdfxml-streaming-parser jsonld rdf-validate-shacl
 * Run:
 *   node scripts/validate-serializations.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as N3 from 'n3';
import { RdfXmlParser } from 'rdfxml-streaming-parser';
import jsonld from 'jsonld';
import shaclPkg from 'rdf-validate-shacl';
const SHACLValidator = shaclPkg.default || shaclPkg;

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const ONT = path.join(ROOT, 'ontology');
const W = 'https://w3id.org/wco-dm/4.3.0#';
const OWL = 'http://www.w3.org/2002/07/owl#';
const RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#';
const SH = 'http://www.w3.org/ns/shacl#';

function parseTurtle(file) {
  return new N3.Parser().parse(fs.readFileSync(path.join(ONT, file), 'utf8'));
}

async function parseRdfXml(file) {
  const quads = [];
  const parser = new RdfXmlParser();
  await new Promise((resolve, reject) => {
    parser.on('data', q => quads.push(q)).on('error', reject).on('end', resolve);
    parser.end(fs.readFileSync(path.join(ONT, file), 'utf8'));
  });
  return quads;
}

async function parseJsonLd(file) {
  const doc = JSON.parse(fs.readFileSync(path.join(ONT, file), 'utf8'));
  const nq = await jsonld.toRDF(doc, { format: 'application/n-quads' });
  return nq.trim().split('\n').filter(Boolean).map(line => {
    const [subject, predicate, object] = line.split(' ').slice(0, 3);
    return { subject: { value: subject }, predicate: { value: predicate }, object: { value: object } };
  });
}

function countTypes(quads) {
  const types = {};
  for (const q of quads) {
    if (q.predicate.value === RDF + 'type') {
      types[q.object.value] = (types[q.object.value] || 0) + 1;
    }
  }
  return types;
}

function integrity(quads) {
  const classes = new Set();
  const dps = new Set();
  for (const q of quads) {
    if (q.predicate.value === RDF + 'type' && q.object.value === OWL + 'Class') classes.add(q.subject.value);
    if (q.predicate.value === RDF + 'type' && q.object.value === OWL + 'DatatypeProperty') dps.add(q.subject.value);
  }
  const missing = [];
  for (const q of quads) {
    if (q.predicate.value === 'http://www.w3.org/2000/01/rdf-schema#range' && q.object.value.startsWith(W + 'C_') && !classes.has(q.object.value)) {
      missing.push(['range', q.object.value]);
    }
    if (q.predicate.value === W + 'usedByClass' && !classes.has(q.object.value)) missing.push(['usedByClass', q.object.value]);
    if (q.predicate.value === W + 'usedByDataElement' && !dps.has(q.object.value)) missing.push(['usedByDataElement', q.object.value]);
  }
  return { classes: classes.size, datatypeProperties: dps.size, missing };
}

async function shaclCheck() {
  const shapes = new N3.Store();
  shapes.addQuads(parseTurtle('wco-dm-4.3.0-shapes.ttl'));
  const results = {};
  for (const file of ['wco-dm-4.3.0-sample.ttl', 'wco-dm-4.3.0-sample-invalid.ttl']) {
    const data = new N3.Store();
    data.addQuads(parseTurtle(file));
    const report = await new SHACLValidator(shapes).validate(data);
    results[file] = {
      conforms: report.conforms,
      results: report.results.length,
      messages: report.results.flatMap(r => r.message.map(m => m.value)),
    };
  }
  return results;
}

async function main() {
  const ttl = parseTurtle('wco-dm-4.3.0.ttl');
  const owl = await parseRdfXml('wco-dm-4.3.0.owl');
  const jsonldQuads = await parseJsonLd('wco-dm-4.3.0.jsonld');
  const profiles = parseTurtle('wco-dm-4.3.0-profiles.ttl');
  const profileShapes = new N3.Store();
  profileShapes.addQuads(parseTurtle('wco-dm-4.3.0-profiles-shapes.ttl'));
  const profileShacl = {};
  for (const file of ['wco-dm-4.3.0-profiles-sample.ttl', 'wco-dm-4.3.0-profiles-sample-invalid.ttl']) {
    const data = new N3.Store();
    data.addQuads(parseTurtle(file));
    const report = await new SHACLValidator(profileShapes).validate(data);
    profileShacl[file] = {
      conforms: report.conforms,
      results: report.results.length,
      messages: report.results.flatMap(r => r.message.map(m => m.value)),
    };
  }
  const report = {
    turtle: { triples: ttl.length, types: countTypes(ttl) },
    rdfxml: { quads: owl.length },
    jsonld: { quads: jsonldQuads.length },
    integrity: integrity(ttl),
    shacl: await shaclCheck(),
    profiles: {
      triples: profiles.length,
      shapesTriples: parseTurtle('wco-dm-4.3.0-profiles-shapes.ttl').length,
      shacl: profileShacl,
    },
    pass: ttl.length === owl.length && ttl.length === jsonldQuads.length && integrity(ttl).missing.length === 0 && profileShacl['wco-dm-4.3.0-profiles-sample.ttl'].conforms === true && profileShacl['wco-dm-4.3.0-profiles-sample-invalid.ttl'].conforms === false,
  };
  console.log(JSON.stringify(report, null, 2));
  if (!report.pass || report.shacl['wco-dm-4.3.0-sample.ttl'].conforms !== true || report.shacl['wco-dm-4.3.0-sample-invalid.ttl'].conforms !== false) {
    process.exitCode = 1;
  }
}

main().catch(err => { console.error(err); process.exit(1); });
