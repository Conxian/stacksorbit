import { describe, expect, it } from 'vitest';
import { Cl } from '@stacks/transactions';

const accounts = simnet.getAccounts();
const deployer = accounts.get('deployer')!;
const wallet1 = accounts.get('wallet_1')!;

describe('placeholder contract', () => {
  it('initializes with the deployer as the owner', async () => {
    const { result } = await simnet.callReadOnlyFn(
      'placeholder',
      'get-owner',
      [],
      deployer
    );
    expect(result).toEqual(Cl.principal(deployer));
  });

  it('returns the same owner regardless of the caller', async () => {
    const { result } = await simnet.callReadOnlyFn(
      'placeholder',
      'get-owner',
      [],
      wallet1
    );
    expect(result).toEqual(Cl.principal(deployer));
  });
});
