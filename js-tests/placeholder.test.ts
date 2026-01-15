import { describe, expect, it } from 'vitest';
import { Cl } from '@stacks/transactions';

describe('placeholder', () => {
  it('should get the owner', async () => {
    const deployerAddress = simnet.getAccounts().get('deployer');
    const { result } = await simnet.callReadOnlyFn(
      'placeholder',
      'get-owner',
      [],
      deployerAddress
    );
    expect(result).toEqual(Cl.principal(deployerAddress));
  });
});
