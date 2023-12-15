export class Parameter {
    name: string = '';
    description: string = '';
    value: string = '';

    constructor(initializer?: any) {
      if (!initializer) return;
      if (initializer.name) this.name = initializer.name;
      if (initializer.description) this.description = initializer.description;
      if (initializer.value) this.value = initializer.value;
    }
  }
