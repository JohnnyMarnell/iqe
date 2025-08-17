import { readFileSync, writeFileSync } from 'fs';
import { JSONPath } from 'jsonpath-plus';

const loadJson = (path: string) => JSON.parse(readFileSync(path, 'utf8'));
const saveJson = (path: string, data: any) => writeFileSync(path, JSON.stringify(data, null, 2));

const findAllByClass = (data: any, className: string, ignoreCase = true) => {
  const pattern = ignoreCase ? className.toLowerCase() : className;
  const results = JSONPath({
    path: '$..[?(@.class)]',
    json: data,
    resultType: 'all'
  });
  
  return results.filter((r: any) => {
    const classValue = ignoreCase ? r.value.class.toLowerCase() : r.value.class;
    return classValue.includes(pattern);
  });
};

const removeByPaths = (data: any, paths: string[]) => {
  paths.forEach(path => {
    const parentPath = path.substring(0, path.lastIndexOf('['));
    const parent = JSONPath({ path: parentPath, json: data })[0];
    if (Array.isArray(parent)) {
      const index = parseInt(path.match(/\[(\d+)\]$/)?.[1] || '-1');
      if (index >= 0) parent.splice(index, 1);
    }
  });
};

// Rectangle bounds based on actual parcan positions
const RECTANGLE = {
  nw: { x: 60, y: 720, z: 20 },       // Northwest corner
  ne: { x: 60, y: 720, z: -1980 },    // Northeast corner  
  se: { x: -2400, y: 720, z: -1980 },  // Southeast corner
  sw: { x: -2400, y: 720, z: 20 }     // Southwest corner
};

// Track DMX channel automatically
let currentDmxChannel = 0;

// Track ID automatically starting from 3001
let currentId = 3001;

// Add a parcan at normalized position (0-1, 0-1) where (0,0) is NW corner
// xNorm: 0 = west edge, 1 = east edge
// yNorm: 0 = north edge, 1 = south edge
const addParcan = (template: any, xNorm: number, yNorm: number) => {
  // Interpolate between corners
  const x = RECTANGLE.nw.x + (RECTANGLE.sw.x - RECTANGLE.nw.x) * yNorm;
  const z = RECTANGLE.nw.z + (RECTANGLE.ne.z - RECTANGLE.nw.z) * xNorm;
  const y = RECTANGLE.nw.y; // Height is constant
  
  const parcan = {
    ...template,
    id: currentId++,
    parameters: {
      ...template.parameters,
      label: `DMX ParCan ${Math.floor(currentDmxChannel / 7) + 1}`,
      x: x,
      y: y,
      z: z,
      dmxChannel: currentDmxChannel
    }
  };
  
  currentDmxChannel += 7; // Auto-increment for next parcan
  return parcan;
};

// Generate corner positions (CCW from NW)
const getCornerPositions = (): Array<[number, number]> => {
  return [
    [0, 0], // NW corner
    [1, 0], // NE corner  
    [1, 1], // SE corner
    [0, 1], // SW corner
  ];
};

// Generate positions along perimeter
const generatePerimeterPositions = (count: number): Array<[number, number]> => {
  const positions: Array<[number, number]> = [];
  
  if (count <= 4) {
    // Just use corners
    return getCornerPositions().slice(0, count);
  }
  
  // Distribute along perimeter
  const perimeter = 4; // Total perimeter in normalized units
  const spacing = perimeter / count;
  
  for (let i = 0; i < count; i++) {
    let distance = i * spacing;
    
    // CCW from NW corner
    if (distance < 1) {
      // North edge (NW to NE)
      positions.push([distance, 0]);
    } else if (distance < 2) {
      // East edge (NE to SE)
      positions.push([1, distance - 1]);
    } else if (distance < 3) {
      // South edge (SE to SW)
      positions.push([1 - (distance - 2), 1]);
    } else {
      // West edge (SW to NW)
      positions.push([0, 1 - (distance - 3)]);
    }
  }
  
  return positions;
};

const pp = (obj: any) => console.log(JSON.stringify(obj, null, 2));

const data = loadJson('./Projects/iqe.lxp');
const parcans = findAllByClass(data, 'parcan');

if (parcans.length > 0) {
  console.log('Existing parcans:');
  pp(parcans.map((p: any) => p.value));
  
  const template = parcans[0].value;
  const paths = parcans.map((p: any) => p.path).reverse();
  
  removeByPaths(data, paths);
  
  const fixturesPath = '$.model.fixtures';
  const fixtures = JSONPath({ path: fixturesPath, json: data })[0];
  
  // Reset counters
  currentDmxChannel = 0;
  currentId = 3001;
  
  // Create list of parcans
  const pcs = [];
  
  // 8 parcans total, starting from SE corner going CCW to SW
  // SE corner
  pcs.push(addParcan(template, 1, 1));   // SE corner
  
  // 6 along north wall (from east to west)
  pcs.push(addParcan(template, 1, 0));   // NE corner
  pcs.push(addParcan(template, 0.8, 0)); // North wall position 1
  pcs.push(addParcan(template, 0.6, 0)); // North wall position 2
  pcs.push(addParcan(template, 0.4, 0)); // North wall position 3
  pcs.push(addParcan(template, 0.2, 0)); // North wall position 4
  pcs.push(addParcan(template, 0, 0));   // NW corner
  
  // SW corner
  pcs.push(addParcan(template, 0, 1));   // SW corner
  
  // Add all parcans to fixtures at once
  fixtures.push(...pcs); 
  
  saveJson('./Projects/iqe_modified.lxp', data);
  console.log('\nSaved to iqe_modified.lxp');
}