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

const createParcan = (template: any, id: number, x: number, y: number, z: number, dmxChannel: number) => ({
  ...template,
  id: id,
  parameters: {
    ...template.parameters,
    label: `DMX ParCan ${dmxChannel / 6 + 1}`,
    x: x * 1000 - 500,  // Convert 0-1 to -500 to 500
    y: y * 1000,        // Convert 0-1 to 0 to 1000
    z: z * 1000 - 500,  // Convert 0-1 to -500 to 500
    dmxChannel: dmxChannel
  }
});

const generatePerimeterPositions = (count: number): Array<[number, number]> => {
  const positions: Array<[number, number]> = [];
  
  if (count === 1) {
    positions.push([0, 0]);
  } else if (count === 2) {
    positions.push([0, 0]);
    positions.push([1, 1]);
  } else {
    const perSide = Math.ceil(count / 4);
    for (let i = 0; i < count; i++) {
      const side = Math.floor(i / perSide);
      const t = (i % perSide) / Math.max(1, perSide - 1);
      
      switch (side) {
        case 0: positions.push([t, 0]); break;         // Bottom edge
        case 1: positions.push([1, t]); break;         // Right edge  
        case 2: positions.push([1 - t, 1]); break;     // Top edge
        case 3: positions.push([0, 1 - t]); break;     // Left edge
      }
    }
  }
  
  return positions;
};

const pp = (obj: any) => console.log(JSON.stringify(obj, null, 2));

const NUM_PARCANS = 2;
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
  
  const positions = generatePerimeterPositions(NUM_PARCANS);
  const newParcans = positions.map((pos, i) => 
    createParcan(template, 3001 + i, pos[0], 0.7, pos[1], i * 6)
  );
  
  console.log('\nNew parcans:');
  pp(newParcans);
  
  fixtures.push(...newParcans);
  
  saveJson('./Projects/iqe_modified.lxp', data);
}