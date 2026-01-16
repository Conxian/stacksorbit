const { initSimnet } = require('@stacks/clarinet-sdk');

beforeAll(async () => {
  global.simnet = await initSimnet();
});
